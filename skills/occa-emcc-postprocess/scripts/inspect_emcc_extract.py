#!/usr/bin/env python3
"""Inspect an OCCA EMCC extract directory without modifying it."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


ERROR_RE = re.compile(r"\b(ORA-\d+|SP2-\d+|Traceback|Exception|ERROR|FAILED)\b", re.I)


def count_csv(path: Path) -> tuple[int, list[str]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        return sum(1 for _ in reader), header


def scan_errors(files: list[Path]) -> list[tuple[Path, int, str]]:
    hits: list[tuple[Path, int, str]] = []
    for path in files:
        with path.open(encoding="utf-8", errors="replace") as handle:
            for lineno, line in enumerate(handle, start=1):
                if ERROR_RE.search(line):
                    hits.append((path, lineno, line.strip()[:240]))
    return hits


def current_availability(extract_dir: Path) -> Counter[tuple[str, str]]:
    path = extract_dir / "emcc_sizing_availability_history.csv"
    counts: Counter[tuple[str, str]] = Counter()
    if not path.exists():
        return counts
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            if not (row.get("END_TIMESTAMP_UTC") or "").strip():
                counts[
                    (
                        (row.get("TARGET_TYPE") or "").strip(),
                        (row.get("AVAILABILITY_STATUS") or "").strip(),
                    )
                ] += 1
    return counts


def metric_ranges(extract_dir: Path) -> list[str]:
    lines: list[str] = []
    for path in sorted(extract_dir.glob("emcc_sizing_metrics_*.csv")):
        rows = 0
        targets: set[str] = set()
        metrics: set[tuple[str, str]] = set()
        min_ts = None
        max_ts = None
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            for row in csv.DictReader(handle):
                rows += 1
                if row.get("TARGET_GUID"):
                    targets.add(row["TARGET_GUID"])
                metrics.add((row.get("METRIC_NAME", ""), row.get("METRIC_COLUMN", "")))
                ts = (row.get("ROLLUP_TIMESTAMP_UTC") or "").strip()
                if ts:
                    min_ts = ts if min_ts is None or ts < min_ts else min_ts
                    max_ts = ts if max_ts is None or ts > max_ts else max_ts
        lines.append(
            f"{path.name}: rows={rows}, targets={len(targets)}, "
            f"metrics={len(metrics)}, min={min_ts}, max={max_ts}"
        )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("work_dir", type=Path)
    parser.add_argument("--show-error-lines", action="store_true")
    args = parser.parse_args()

    extract_dir = args.work_dir / "emcc_sizing_extracts"
    if not extract_dir.is_dir():
        raise SystemExit(f"Missing directory: {extract_dir}")

    csv_files = sorted(extract_dir.glob("*.csv"))
    txt_files = sorted(extract_dir.glob("*.txt"))
    print(f"extract_dir={extract_dir}")
    print(f"csv_files={len(csv_files)}")
    print(f"txt_files={len(txt_files)}")

    print("\nCSV inventory")
    for path in csv_files:
        rows, header = count_csv(path)
        print(f"{path.name}: rows={rows}, cols={len(header)}, header={'|'.join(header[:8])}")

    hits = scan_errors(csv_files + txt_files)
    print(f"\nerror_like_matches={len(hits)}")
    if args.show_error_lines:
        for path, lineno, text in hits:
            print(f"{path.name}:{lineno}: {text}")

    print("\nCurrent availability")
    for (target_type, status), count in sorted(current_availability(extract_dir).items()):
        print(f"{target_type or '<blank>'} / {status or '<blank>'}: {count}")

    print("\nMetric ranges")
    for line in metric_ranges(extract_dir):
        print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
