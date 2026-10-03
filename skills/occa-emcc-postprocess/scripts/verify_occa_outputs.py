#!/usr/bin/env python3
"""Verify OCCA EMCC post-processing outputs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


KEY_FILES = [
    "occa_sizing_output/sizing/databases.csv",
    "occa_sizing_output/sizing/instances.csv",
    "occa_sizing_output/sizing/servers.csv",
    "occa_sizing_output/sizing/metric_presence_by_stage.csv",
    "occa_sizing_output/sizing/sizing.csv",
    "occa_sizing_output/sizing/database_rollups.csv",
    "occa_sizing_output/sizing/cohort_rollups.csv",
    "occa_sizing_output/sizing/database_statistics.csv",
    "occa_sizing_output/sizing/cohort_statistics.csv",
]

REQUIRED_OVERRIDE_FIELDS = {
    "properties_database.csv": ("Allocated Database Size (GB)", "Total Database Size (GB)"),
    "properties_instance.csv": ("vCPU", "SGA (MB)", "PGA (MB)", "IOPS", "Logons"),
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def row_counts(path: Path) -> tuple[int, int, int]:
    rows = read_rows(path)
    negative = sum(1 for row in rows if any(str(value).strip() == "-1" for value in row.values()))
    excluded = sum(
        1 for row in rows
        if (row.get("excluded") or row.get("Excluded") or "").strip().lower() == "excluded"
    )
    return len(rows), negative, excluded


def included_missing_override_count(path: Path, excluded_databases: set[str]) -> int:
    rows = read_rows(path)
    fields = REQUIRED_OVERRIDE_FIELDS[path.name]
    return sum(
        1 for row in rows
        if (row.get("Cohort") or "included").strip().lower() not in ("excluded", "unassigned")
        and (row.get("Database Name") or "").strip() not in excluded_databases
        and any(str(row.get(field, "")).strip() == "-1" for field in fields)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("work_dir", type=Path)
    args = parser.parse_args()

    failures = 0
    for rel in KEY_FILES:
        path = args.work_dir / rel
        if not path.exists():
            print(f"{rel}: MISSING")
            failures += 1
            continue
        rows, negative, excluded = row_counts(path)
        print(f"{rel}: rows={rows} negative_rows={negative} excluded_rows={excluded}")

    db_properties = args.work_dir / "occa_sizing_properties/properties_database.csv"
    excluded_databases = set()
    if db_properties.exists():
        excluded_databases = {
            (row.get("Database Name") or "").strip()
            for row in read_rows(db_properties)
            if (row.get("Cohort") or "").strip().lower() in ("", "excluded", "unassigned")
        }

    for rel in [
        "occa_sizing_properties/properties_database.csv",
        "occa_sizing_properties/properties_instance.csv",
    ]:
        path = args.work_dir / rel
        if not path.exists():
            print(f"{rel}: MISSING")
            failures += 1
            continue
        rows, negative, excluded = row_counts(path)
        unresolved = included_missing_override_count(path, excluded_databases)
        print(f"{rel}: rows={rows} negative_rows={negative} unresolved_included_rows={unresolved}")
        if unresolved:
            failures += 1

    plot_count = len(list((args.work_dir / "occa_sizing_output" / "plots").glob("**/*.html")))
    print(f"html_plots={plot_count}")
    if plot_count == 0:
        failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
