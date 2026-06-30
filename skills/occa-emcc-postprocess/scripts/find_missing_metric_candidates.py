#!/usr/bin/env python3
"""Find OCCA missing metric markers and likely replacement candidates."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


REQUIRED_INSTANCE_COLS = ["vCPU", "SGA (MB)", "PGA (MB)", "IOPS", "Logons"]
REQUIRED_DATABASE_COLS = ["Allocated Database Size (GB)", "Total Database Size (GB)"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def negative_cols(row: dict[str, str]) -> list[str]:
    return [key for key, value in row.items() if str(value).strip() == "-1"]


def availability_by_guid(extract_dir: Path) -> dict[str, Counter[str]]:
    path = extract_dir / "emcc_sizing_availability_history.csv"
    out: dict[str, Counter[str]] = defaultdict(Counter)
    for row in read_csv(path):
        guid = row.get("TARGET_GUID", "")
        out[guid][row.get("AVAILABILITY_STATUS", "")] += 1
        if not (row.get("END_TIMESTAMP_UTC") or "").strip():
            out[guid][f"CURRENT:{row.get('AVAILABILITY_STATUS', '')}"] += 1
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("work_dir", type=Path)
    args = parser.parse_args()

    props_dir = args.work_dir / "occa_sizing_properties"
    extract_dir = args.work_dir / "emcc_sizing_extracts"
    db_rows = read_csv(props_dir / "properties_database.csv")
    inst_rows = read_csv(props_dir / "properties_instance.csv")
    dg_rows = read_csv(extract_dir / "emcc_sizing_structure_db_dr.csv")
    availability = availability_by_guid(extract_dir)

    db_by_name = {row.get("Database Name", ""): row for row in db_rows}
    inst_by_db: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in inst_rows:
        inst_by_db[row.get("Database Name", "")].append(row)

    print("DATABASE_ROWS_WITH_NEGATIVE_MARKERS")
    for row in db_rows:
        neg = negative_cols(row)
        if not neg:
            continue
        db_name = row.get("Database Name", "")
        print(
            {
                "database": db_name,
                "negative_columns": neg,
                "cohort": row.get("Cohort", ""),
                "standby_type": row.get("cdb_standby_type", ""),
                "target_guid": row.get("target_guid", ""),
            }
        )
        for dg in dg_rows:
            if dg.get("STDBY_TARGET_NAME") == db_name or dg.get("STDBY_TARGET_GUID") == row.get("target_guid"):
                primary_name = dg.get("PRI_TARGET_NAME") or dg.get("PRI_DB_UNIQUE_NAME")
                primary_candidates = [
                    name for name in db_by_name if primary_name and primary_name.lower() in name.lower()
                ]
                print(
                    "  data_guard_candidate=",
                    {
                        "primary_hint": primary_name,
                        "primary_candidates": primary_candidates,
                        "scope": "Physical Standby",
                    },
                )

    print("\nINSTANCE_ROWS_WITH_NEGATIVE_MARKERS")
    for row in inst_rows:
        neg = negative_cols(row)
        if not neg:
            continue
        db_name = row.get("Database Name", "")
        instance = row.get("Instance", "")
        siblings = []
        for sibling in inst_by_db.get(db_name, []):
            if sibling.get("Instance") == instance:
                continue
            sibling_neg = negative_cols(sibling)
            siblings.append(
                {
                    "instance": sibling.get("Instance", ""),
                    "negative_columns": sibling_neg,
                    "status": sibling.get("status", ""),
                    "server": sibling.get("Server Name", ""),
                }
            )
        print(
            {
                "database": db_name,
                "instance": instance,
                "negative_columns": neg,
                "status": row.get("status", ""),
                "server": row.get("Server Name", ""),
                "availability": dict(availability.get(row.get("target_guid", ""), Counter())),
                "sibling_candidates": siblings,
            }
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
