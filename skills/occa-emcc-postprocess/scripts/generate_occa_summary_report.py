#!/usr/bin/env python3
"""Generate an OCCA current-state summary dashboard from sizing outputs."""

from __future__ import annotations

import argparse
import csv
import html
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path


COLORS = ["#C74634", "#312D2A", "#D4712A", "#437C94", "#6B6B6B", "#8F6A38", "#5F7D4F"]


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def pick(row: dict[str, str], *aliases: str) -> str:
    if not row:
        return ""
    normalized = {normalize(key): key for key in row}
    for alias in aliases:
        key = normalized.get(normalize(alias))
        if key is not None and str(row.get(key, "")).strip():
            return row.get(key, "")
    for alias in aliases:
        wanted = normalize(alias)
        for norm_key, original_key in normalized.items():
            if wanted and (wanted in norm_key or norm_key in wanted) and str(row.get(original_key, "")).strip():
                return row.get(original_key, "")
    return ""


def number(value: str | int | float | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).strip().replace(",", "")
    if cleaned in {"", "-"}:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def fmt(value: str | int | float, decimals: int = 1) -> str:
    numeric = number(value)
    if abs(numeric - round(numeric)) < 0.005:
        return f"{int(round(numeric)):,}"
    return f"{numeric:,.{decimals}f}"


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""))


def rel_link(path: Path, output_path: Path) -> str:
    try:
        return path.resolve().relative_to(output_path.resolve().parent).as_posix()
    except ValueError:
        return path.resolve().as_uri()


def classify_standby(value: str) -> str:
    lower = value.lower()
    if "primary" in lower:
        return "Primary"
    if "standby" in lower:
        return "Physical Standby"
    return "N/A"


def database_record(row: dict[str, str], instance_counts: dict[str, int]) -> dict[str, object]:
    db_name = pick(row, "database", "database name", "db name", "target name", "name", "cdb")
    sga = number(pick(row, "sga gb", "sga (gb)", "max sga gb", "sga"))
    pga = number(pick(row, "pga gb", "pga (gb)", "max pga gb", "pga"))
    memory = number(pick(row, "memory gb", "db memory gb", "db memory (gb)", "sga+pga gb"))
    if not memory:
        memory = sga + pga
    instances = number(pick(row, "instances", "instance count", "num instances"))
    if not instances and db_name:
        instances = instance_counts.get(db_name, 0)
    return {
        "database": db_name,
        "cohort": pick(row, "cohort", "cohort name", "cdb_cohort") or "Unassigned",
        "version": pick(row, "database version", "db version", "cdb_version_sizing", "cdb_version", "version"),
        "instances": instances,
        "vcpu": number(pick(row, "DB vCPU", "max vcpu", "vcpu", "total vcpu", "cpu", "max cpu")),
        "sga": sga,
        "pga": pga,
        "memory": memory,
        "iops": number(pick(row, "DB IOPS", "iops", "total iops", "max iops")),
        "logons": number(pick(row, "DB Logons", "logons", "total logons", "sessions", "max logons")),
        "allocated": number(pick(row, "Allocated Storage (GB)", "allocated gb", "allocated (gb)", "allocated storage gb", "allocated storage", "cdb_size_allocated_gb_telemetry")),
        "used": number(pick(row, "Used Storage (GB)", "used gb", "used (gb)", "used storage gb", "used storage", "cdb_size_used_gb_telemetry")),
        "standby": classify_standby(pick(row, "db standby type", "standby type", "database role", "role", "cdb_standby_type")),
        "cluster": pick(row, "cluster", "cluster name", "host cluster"),
    }


def server_record(row: dict[str, str], instance_rows: list[dict[str, str]]) -> dict[str, object]:
    server = pick(row, "server", "server name", "host", "host name", "target name", "name")
    related_instances = [
        inst for inst in instance_rows if pick(inst, "server", "server name", "host", "host name") == server
    ]
    primary = standby = unknown = 0
    for inst in related_instances:
        status = classify_standby(pick(inst, "db standby type", "standby type", "database role", "role"))
        if status == "Primary":
            primary += 1
        elif status == "Physical Standby":
            standby += 1
        else:
            unknown += 1
    memory_used = number(pick(row, "memory used gb", "db memory gb", "memory used (gb)"))
    if not memory_used:
        memory_used = sum(
            (
                number(pick(inst, "db_sga_mb_telemetry", "SGA (MB)", "sga mb"))
                + number(pick(inst, "db_pga_mb_telemetry", "PGA (MB)", "pga mb"))
            )
            / 1024
            for inst in related_instances
        )
    max_vcpu = number(pick(row, "max vcpu used", "max vcpu", "vcpu used"))
    if not max_vcpu:
        max_vcpu = sum(number(pick(inst, "db_vcpu_telemetry", "vCPU", "vcpu")) for inst in related_instances)
    return {
        "cohort": pick(row, "cohort", "cohort name", "cluster") or "Unassigned",
        "cluster": pick(row, "cluster", "cluster name") or pick(row, "cohort", "cohort name") or "Unassigned",
        "server": server,
        "instances": len(related_instances) or number(pick(row, "db instances", "instances", "instance count")),
        "primary": primary,
        "standby": standby,
        "unknown": unknown,
        "cpu_type": pick(row, "cpu type", "processor type", "cpu"),
        "chips": number(pick(row, "physical_cpu_count", "chips", "sockets", "cpu chips", "Chip Count (Actual)")),
        "cores_per_chip": number(pick(row, "cores_per_chip", "cores/chip", "cores per chip", "Cores Per Chip (Actual)")),
        "cores": number(pick(row, "total_cpu_cores", "total cores", "cores", "cpu cores")),
        "total_vcpu": number(pick(row, "logical_cpu_count", "total vcpu", "vcpu", "cpu threads")),
        "max_vcpu": max_vcpu,
        "memory": number(pick(row, "mem_gb", "memory gb", "memory (gb)", "ram gb", "physical memory gb")),
        "memory_used": memory_used,
        "os": pick(row, "os version", "operating system", "platform"),
        "status": pick(row, "host_status", "status", "target status", "availability status"),
    }


def selected_rollups(rows: list[dict[str, str]], adjusted: str = "N") -> list[dict[str, str]]:
    candidates = [
        row
        for row in rows
        if pick(row, "Adjusted Values").upper() == adjusted
        and pick(row, "Rollup Type").upper() == "AVERAGE"
        and pick(row, "Time Unit").upper() == "HOURLY"
        and pick(row, "Time Period") == "3"
    ]
    if candidates:
        return candidates
    candidates = [row for row in rows if pick(row, "Adjusted Values").upper() == adjusted]
    return candidates or rows


def mb_to_gb(value: str | int | float | None) -> float:
    return number(value) / 1024


def build_model(work_dir: Path, output_path: Path) -> dict[str, object]:
    sizing_dir = work_dir / "occa_sizing_output" / "sizing"
    databases = read_rows(sizing_dir / "databases.csv")
    instances = read_rows(sizing_dir / "instances.csv")
    servers = read_rows(sizing_dir / "servers.csv")
    database_rollups = selected_rollups(read_rows(sizing_dir / "database_rollups.csv"), "N")
    cohort_rollups = selected_rollups(read_rows(sizing_dir / "cohort_rollups.csv"), "N")
    if not databases:
        raise FileNotFoundError(f"Required OCCA file is missing or empty: {sizing_dir / 'databases.csv'}")

    instance_counts: dict[str, int] = defaultdict(int)
    for row in instances:
        db_name = pick(row, "database", "database name", "db name")
        if db_name:
            instance_counts[db_name] += 1

    metadata_by_db = {pick(row, "cdb", "database", "name"): row for row in databases}
    db_records = []
    if database_rollups:
        for row in database_rollups:
            name = pick(row, "Name", "database", "cdb")
            metadata = metadata_by_db.get(name, {})
            record = database_record({**metadata, **row}, instance_counts)
            record.update(
                {
                    "database": name,
                    "cohort": pick(row, "Cohort", "cdb_cohort") or record["cohort"],
                    "instances": number(pick(row, "Instances Included", "instances")),
                    "allocated": number(pick(row, "Allocated Storage (GB)")),
                    "used": number(pick(row, "Used Storage (GB)")),
                    "vcpu": number(pick(row, "DB vCPU")),
                    "sga": mb_to_gb(pick(row, "DB SGA (MB)")),
                    "pga": mb_to_gb(pick(row, "DB PGA (MB)")),
                    "memory": mb_to_gb(pick(row, "DB Memory (MB)")),
                    "iops": number(pick(row, "DB IOPS")),
                    "logons": number(pick(row, "DB Logons")),
                }
            )
            db_records.append(record)
    else:
        db_records = [database_record(row, instance_counts) for row in databases]
    server_records = [server_record(row, instances) for row in servers]
    cohorts: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    if cohort_rollups:
        for row in cohort_rollups:
            cohort = pick(row, "Name", "Cohort") or "Unassigned"
            cohorts[cohort]["dbs"] = number(pick(row, "Databases Included"))
            cohorts[cohort]["instances"] = number(pick(row, "Instances Included"))
            cohorts[cohort]["allocated"] = number(pick(row, "Allocated Storage (GB)"))
            cohorts[cohort]["used"] = number(pick(row, "Used Storage (GB)"))
            cohorts[cohort]["vcpu"] = number(pick(row, "DB vCPU"))
            cohorts[cohort]["sga"] = mb_to_gb(pick(row, "DB SGA (MB)"))
            cohorts[cohort]["pga"] = mb_to_gb(pick(row, "DB PGA (MB)"))
            cohorts[cohort]["memory"] = mb_to_gb(pick(row, "DB Memory (MB)"))
            cohorts[cohort]["iops"] = number(pick(row, "DB IOPS"))
            cohorts[cohort]["logons"] = number(pick(row, "DB Logons"))
    for row in db_records:
        cohort = str(row["cohort"])
        if not cohort_rollups:
            cohorts[cohort]["dbs"] += 1
            cohorts[cohort]["instances"] += number(row["instances"])
            for key in ["allocated", "used", "vcpu", "sga", "pga", "memory", "iops", "logons"]:
                cohorts[cohort][key] += number(row[key])
        cohorts[cohort]["primary"] += 1 if row["standby"] == "Primary" else 0
        cohorts[cohort]["standby"] += 1 if row["standby"] == "Physical Standby" else 0
        cohorts[cohort]["unknown"] += 1 if row["standby"] == "N/A" else 0
        cohorts[cohort]["max_logons"] = max(cohorts[cohort]["max_logons"], number(row["logons"]))

    plots = sorted((work_dir / "occa_sizing_output" / "plots").glob("**/*.html"))
    vcpu_plots = [path for path in plots if "vcpu" in path.name.lower()]
    multiplier_plots = [path for path in plots if "multiplier" in path.name.lower() or "adjustment" in path.name.lower()]
    source_files = sorted(sizing_dir.glob("*.csv"))
    return {
        "work_dir": work_dir,
        "output_path": output_path,
        "db_records": db_records,
        "server_records": server_records,
        "cohorts": dict(sorted(cohorts.items())),
        "plots": plots,
        "vcpu_plots": vcpu_plots,
        "multiplier_plots": multiplier_plots,
        "source_files": source_files,
    }


def card(value: object, label: str, title: str) -> str:
    return (
        f'<div class="card" title="{esc(title)}"><span class="help-icon">&#9432;</span>'
        f'<div class="value">{esc(value)}</div><div class="label">{esc(label)}</div></div>'
    )


def cohort_badge(name: str, index: int) -> str:
    color = COLORS[index % len(COLORS)]
    return f'<span class="cohort-badge" style="background: {color}; color: white;">{esc(name)}</span>'


def table(headers: list[str], rows: list[list[object]], table_id: str) -> str:
    head = "".join(f"<th>{esc(header)}</th>" for header in headers)
    body = []
    for row in rows:
        cells = []
        for value in row:
            css = ' class="number"' if isinstance(value, (int, float)) else ""
            text = fmt(value) if isinstance(value, (int, float)) else value
            cells.append(f"<td{css}>{text}</td>")
        body.append(f"<tr>{''.join(cells)}</tr>")
    return f'<table id="{esc(table_id)}"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>'


def render_plot_cards(paths: list[Path], output_path: Path) -> str:
    if not paths:
        return '<p class="empty">No matching OCCA plot HTML files were found.</p>'
    cards = []
    for path in paths:
        link = rel_link(path, output_path)
        title = path.stem.replace("_", " ")
        cards.append(
            '<div class="plot-card">'
            f'<h3>{esc(title)}</h3>'
            f'<iframe src="{esc(link)}"></iframe>'
            f'<a href="{esc(link)}" target="_blank" rel="noopener">Open full plot</a>'
            "</div>"
        )
    return "".join(cards)


def render(model: dict[str, object]) -> str:
    db_records = model["db_records"]
    server_records = model["server_records"]
    cohorts = model["cohorts"]
    output_path = model["output_path"]
    total = defaultdict(float)
    for row in db_records:
        total["dbs"] += 1
        total["instances"] += number(row["instances"])
        total["primary"] += 1 if row["standby"] == "Primary" else 0
        total["standby"] += 1 if row["standby"] == "Physical Standby" else 0
        total["unknown"] += 1 if row["standby"] == "N/A" else 0
    if cohorts:
        total["dbs"] = sum(number(row["dbs"]) for row in cohorts.values())
        total["instances"] = sum(number(row["instances"]) for row in cohorts.values())
        for key in ["allocated", "used", "memory", "vcpu", "iops", "logons"]:
            total[key] = sum(number(row[key]) for row in cohorts.values())
    else:
        for row in db_records:
            for key in ["allocated", "used", "memory", "vcpu", "iops", "logons"]:
                total[key] += number(row[key])

    cohort_rows = []
    for idx, (name, row) in enumerate(cohorts.items()):
        avg_logons = row["logons"] / row["dbs"] if row["dbs"] else 0
        cohort_rows.append(
            [
                cohort_badge(name, idx),
                row["dbs"],
                row["instances"],
                row["primary"],
                row["standby"],
                row["unknown"],
                row["allocated"],
                row["used"],
                row["vcpu"],
                row["sga"],
                row["pga"],
                row["memory"],
                row["iops"],
                row["logons"],
                row["max_logons"],
                avg_logons,
            ]
        )

    db_rows = []
    color_index = {name: idx for idx, name in enumerate(cohorts)}
    for row in db_records:
        db_rows.append(
            [
                esc(row["database"]),
                cohort_badge(str(row["cohort"]), color_index.get(str(row["cohort"]), 0)),
                esc(row["version"]),
                row["instances"],
                row["vcpu"],
                row["sga"],
                row["pga"],
                row["memory"],
                row["iops"],
                row["logons"],
                row["allocated"],
                row["used"],
                esc(row["standby"]),
                esc(row["cluster"]),
            ]
        )

    server_rows = [
        [
            esc(row["cohort"]),
            esc(row["cluster"]),
            esc(row["server"]),
            row["instances"],
            row["primary"],
            row["standby"],
            row["unknown"],
            esc(row["cpu_type"]),
            row["chips"],
            row["cores_per_chip"],
            row["cores"],
            row["total_vcpu"],
            row["max_vcpu"],
            row["memory"],
            row["memory_used"],
            esc(row["os"]),
            esc(row["status"]),
        ]
        for row in server_records
    ]

    source_links = []
    for path in model["source_files"]:
        link = rel_link(path, output_path)
        source_links.append(f'<li><a href="{esc(link)}" target="_blank" rel="noopener">{esc(path.name)}</a></li>')
    for path in model["plots"]:
        link = rel_link(path, output_path)
        source_links.append(f'<li><a href="{esc(link)}" target="_blank" rel="noopener">{esc(path.relative_to(model["work_dir"]))}</a></li>')

    cards = "\n".join(
        [
            card(fmt(total["dbs"]), "Databases", "Total number of unique databases discovered across all cohorts"),
            card(fmt(total["instances"]), "Instances", "Total database instances, including RAC nodes"),
            card(fmt(total["primary"]), "Primary", "Databases identified as Primary"),
            card(fmt(total["standby"]), "Physical Standby", "Databases identified as Physical Standby"),
            card(fmt(total["unknown"]), "Standby N/A", "Databases with no primary or standby role identified"),
            card(fmt(len(server_records)), "Servers", "Total number of servers in OCCA server output"),
            card(fmt(len(cohorts)), "Cohorts", "Number of cohort groupings used for migration planning"),
            card(fmt(total["allocated"]), "Allocated (GB)", "Total allocated database storage"),
            card(fmt(total["used"]), "Used (GB)", "Total used database storage"),
            card(fmt(total["memory"]), "DB Memory (GB)", "Combined SGA and PGA memory allocation"),
            card(fmt(total["vcpu"]), "Total vCPU", "Sum of database vCPU requirements"),
            card(fmt(total["iops"]), "Total IOPS", "Sum of database IOPS"),
            card(fmt(total["logons"]), "Total Logons", "Sum of database logon sessions"),
        ]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OCCA Current State Dashboard</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #F7F7F7; color: #333; }}
.header {{ background: linear-gradient(135deg, #312D2A 0%, #C74634 100%); color: white; padding: 30px; text-align: center; }}
.header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
.subtitle {{ opacity: .9; font-size: 1.1em; margin-top: 8px; }}
.container {{ max-width: 1600px; margin: 0 auto; padding: 20px; }}
.tab-buttons {{ display: flex; gap: 5px; border-bottom: 2px solid #C74634; flex-wrap: wrap; }}
.tab-btn {{ padding: 12px 24px; background: #e0e5eb; border: none; border-radius: 8px 8px 0 0; cursor: pointer; font-size: 1em; font-weight: 600; color: #312D2A; }}
.tab-btn.active, .tab-btn:hover {{ background: #C74634; color: white; }}
.tab-content {{ display: none; padding: 20px 0; }}
.tab-content.active {{ display: block; }}
.summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); column-gap: 24px; row-gap: 15px; margin: 20px 0; }}
.card {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,.1); text-align: center; position: relative; cursor: help; }}
.card .value {{ font-size: 2em; font-weight: bold; color: #C74634; }}
.card .label {{ color: #666; margin-top: 5px; font-size: .85em; }}
.help-icon {{ position: absolute; top: 8px; right: 10px; color: #bbb; font-size: .8em; }}
.section {{ background: white; border-radius: 8px; padding: 25px; margin: 20px 0; box-shadow: 0 4px 15px rgba(0,0,0,.1); overflow-x: auto; }}
.section h2 {{ color: #C74634; margin-bottom: 20px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }}
table {{ width: 100%; border-collapse: collapse; font-size: .9em; margin-bottom: 15px; }}
th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #e0e0e0; white-space: nowrap; }}
th {{ background: #f8f9fa; color: #312D2A; font-weight: 600; cursor: pointer; }}
tr:hover {{ background: #f8f9fa; }}
.number {{ text-align: right; font-family: Consolas, monospace; }}
.cohort-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: .9em; font-weight: 500; }}
.search-bar {{ display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }}
.search-bar input {{ padding: 8px 14px; border: 1px solid #ccc; border-radius: 6px; font-size: .9em; width: min(420px, 100%); }}
.export-btn {{ background: #474747; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: .85em; font-weight: 500; float: right; margin-top: -42px; }}
.export-btn:hover {{ background: #C74634; }}
.plot-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 20px; }}
.plot-card {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,.1); }}
.plot-card h3 {{ color: #474747; margin-bottom: 10px; }}
.plot-card iframe {{ width: 100%; height: 360px; border: 1px solid #ddd; border-radius: 6px; background: white; }}
.plot-card a, .source-list a {{ color: #C74634; font-weight: 600; }}
.source-list {{ columns: 2; padding-left: 20px; line-height: 1.8; }}
.empty {{ color: #666; padding: 10px 0; }}
.footer {{ text-align: center; padding: 20px; color: #666; font-size: .9em; }}
@media (max-width: 720px) {{
  .header h1 {{ font-size: 1.8em; }}
  .tab-btn {{ flex: 1 1 auto; border-radius: 6px; }}
  .plot-grid {{ grid-template-columns: 1fr; }}
  .source-list {{ columns: 1; }}
}}
</style>
</head>
<body>
<div class="header">
  <h1>OCCA Current State Dashboard</h1>
  <div class="subtitle">Oracle Database Metrics Summary by Cohort</div>
  <div class="subtitle">Generated: {esc(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}</div>
</div>
<div class="container">
  <div class="tab-buttons">
    <button class="tab-btn active" onclick="showTab(event, 'summary')">Summary</button>
    <button class="tab-btn" onclick="showTab(event, 'db-metrics')">Database Metrics</button>
    <button class="tab-btn" onclick="showTab(event, 'servers')">Servers</button>
    <button class="tab-btn" onclick="showTab(event, 'vcpu-graphs')">vCPU Graphs</button>
    <button class="tab-btn" onclick="showTab(event, 'multiplier-graphs')">OCCA Sizing Multiplier</button>
    <button class="tab-btn" onclick="showTab(event, 'sizing-output')">Sizing Output</button>
  </div>
  <div id="summary" class="tab-content active">
    <div class="summary-cards">{cards}</div>
    <div class="section">
      <h2>Database Metrics by Cohort</h2>
      <button class="export-btn" onclick="exportTableToCSV('cohort-metrics-table', 'database_metrics_by_cohort.csv')">Export CSV</button>
      <div class="search-bar"><span>&#128269;</span><input type="text" placeholder="Search cohorts..." oninput="filterTable('cohort-metrics-table', this.value)"></div>
      {table(["Cohort", "DBs", "Instances", "Primary", "Standby", "N/A", "Allocated (GB)", "Used (GB)", "Total vCPU", "SGA (GB)", "PGA (GB)", "Memory (GB)", "Total IOPS", "Total Logons", "Max Logons", "Avg Logons"], cohort_rows, "cohort-metrics-table")}
    </div>
  </div>
  <div id="db-metrics" class="tab-content">
    <div class="section">
      <h2>Database Metrics</h2>
      <button class="export-btn" onclick="exportTableToCSV('db-metrics-table', 'database_metrics.csv')">Export CSV</button>
      <div class="search-bar"><span>&#128269;</span><input type="text" placeholder="Search databases, cohorts, clusters..." oninput="filterTable('db-metrics-table', this.value)"></div>
      {table(["Database", "Cohort", "Version", "Instances", "Max vCPU", "SGA (GB)", "PGA (GB)", "Memory (GB)", "IOPS", "Logons", "Allocated (GB)", "Used (GB)", "DB Standby Type", "Cluster"], db_rows, "db-metrics-table")}
    </div>
  </div>
  <div id="servers" class="tab-content">
    <div class="summary-cards">
      {card(fmt(len(server_records)), "Total Servers", "Total number of servers hosting Oracle databases")}
      {card(fmt(sum(number(row["cores"]) for row in server_records)), "Total CPU Cores", "Sum of CPU cores across all servers")}
      {card(fmt(sum(number(row["memory"]) for row in server_records)), "Total Memory (GB)", "Sum of physical memory across all servers")}
      {card(fmt(sum(number(row["max_vcpu"]) for row in server_records)), "Total vCPU Used", "Sum of max vCPU used across all servers")}
    </div>
    <div class="section">
      <h2>Server Details</h2>
      <button class="export-btn" onclick="exportTableToCSV('servers-table', 'server_details.csv')">Export CSV</button>
      <div class="search-bar"><span>&#128269;</span><input type="text" placeholder="Search servers, cohorts, clusters..." oninput="filterTable('servers-table', this.value)"></div>
      {table(["Cohort", "Cluster", "Server Name", "DB Instances", "Primary", "Standby", "N/A", "CPU Type", "Chips", "Cores/Chip", "Total Cores", "Total vCPU", "Max vCPU Used", "Memory (GB)", "Memory Used (GB)", "OS Version", "Status"], server_rows, "servers-table")}
    </div>
  </div>
  <div id="vcpu-graphs" class="tab-content"><div class="plot-grid">{render_plot_cards(model["vcpu_plots"], output_path)}</div></div>
  <div id="multiplier-graphs" class="tab-content"><div class="plot-grid">{render_plot_cards(model["multiplier_plots"], output_path)}</div></div>
  <div id="sizing-output" class="tab-content">
    <div class="section">
      <h2>Sizing Output</h2>
      <p class="empty">Links below point to the real OCCA output files under this work directory.</p>
      <ul class="source-list">{"".join(source_links)}</ul>
    </div>
  </div>
</div>
<div class="footer"><p>Generated by OCCA Analysis Agent</p></div>
<script>
function showTab(evt, tabId) {{
  document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.getElementById(tabId).classList.add('active');
  evt.target.classList.add('active');
}}
function filterTable(tableId, query) {{
  const q = query.toLowerCase();
  document.querySelectorAll('#' + tableId + ' tbody tr').forEach(row => {{
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}}
document.querySelectorAll('th').forEach((th, index) => {{
  th.addEventListener('click', () => {{
    const table = th.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const numeric = rows.every(row => !isNaN(parseFloat(row.children[index].textContent.replace(/,/g, ''))));
    const asc = th.dataset.asc !== 'true';
    rows.sort((a, b) => {{
      const av = a.children[index].textContent.trim().replace(/,/g, '');
      const bv = b.children[index].textContent.trim().replace(/,/g, '');
      const result = numeric ? parseFloat(av || 0) - parseFloat(bv || 0) : av.localeCompare(bv);
      return asc ? result : -result;
    }});
    th.dataset.asc = asc;
    rows.forEach(row => tbody.appendChild(row));
  }});
}});
function exportTableToCSV(tableId, filename) {{
  const rows = Array.from(document.querySelectorAll('#' + tableId + ' tr'));
  const csv = rows.map(row => Array.from(row.children).map(cell => '"' + cell.textContent.replace(/"/g, '""').trim() + '"').join(',')).join('\\n');
  const blob = new Blob([csv], {{ type: 'text/csv' }});
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
}}
</script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work_dir", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, help="Output HTML path. Defaults to <work_dir>/Sizing.html.")
    args = parser.parse_args()

    work_dir = args.work_dir.resolve()
    output_path = (args.output or work_dir / "Sizing.html").resolve()
    try:
        model = build_model(work_dir, output_path)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 1
    output_path.write_text(render(model), encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
