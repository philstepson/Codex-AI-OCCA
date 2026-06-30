#!/usr/bin/env python3
"""Assign OCCA database cohorts from cluster names with backup and dry-run mode."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
from collections import Counter
from pathlib import Path


BAD_CLUSTER_VALUES = {"", "none", "nan", "null"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("work_dir", type=Path)
    parser.add_argument("--apply", action="store_true", help="write changes")
    args = parser.parse_args()

    path = args.work_dir / "occa_sizing_properties" / "properties_database.csv"
    if not path.exists():
        raise SystemExit(f"Missing editable database properties: {path}")

    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if "Cohort" not in fieldnames or "cluster" not in fieldnames:
        raise SystemExit("Required columns missing: Cohort and/or cluster")

    clusters = [(row.get("cluster") or "").strip() for row in rows]
    missing = [value for value in clusters if value.lower() in BAD_CLUSTER_VALUES]
    counts = Counter(value for value in clusters if value.lower() not in BAD_CLUSTER_VALUES)

    print(f"rows={len(rows)}")
    print(f"cluster_populated={len(rows) - len(missing)}")
    print(f"cluster_blank_or_none={len(missing)}")
    print(f"unique_clusters={len(counts)}")
    print("cohort_counts:")
    for cohort, count in sorted(counts.items()):
        print(f"  {cohort}: {count}")

    if missing:
        raise SystemExit("Cluster values are missing; do not apply cluster cohorts automatically.")

    if not args.apply:
        print("dry_run=true")
        return 0

    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S_UTC")
    backup = path.with_name(f"properties_database.before_cluster_cohorts.{timestamp}.csv")
    shutil.copy2(path, backup)

    changed = 0
    for row in rows:
        new = (row.get("cluster") or "").strip()
        old = (row.get("Cohort") or "").strip()
        if old != new:
            changed += 1
        row["Cohort"] = new

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"backup={backup}")
    print(f"changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
