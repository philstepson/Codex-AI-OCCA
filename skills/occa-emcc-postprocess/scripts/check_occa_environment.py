#!/usr/bin/env python3
"""Check local Python and OCCA CLI prerequisites."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


RELEASE_URL = "https://occa.us.oracle.com/ords/r/occa/occa/occa-releases"


def parse_min_python(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)", value.strip())
    if not match:
        raise argparse.ArgumentTypeError("Use MAJOR.MINOR, for example 3.12")
    return int(match.group(1)), int(match.group(2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-python", type=parse_min_python, default=(3, 12))
    parser.add_argument("--occa", default="occa", help="Path to occa executable")
    parser.add_argument("--release-url", default=RELEASE_URL)
    args = parser.parse_args()

    failures = 0
    current = sys.version_info[:2]
    print(f"python_executable={sys.executable}")
    print(f"python_version={sys.version.split()[0]}")
    print(f"python_minimum={args.min_python[0]}.{args.min_python[1]}")
    if current < args.min_python:
        print("ERROR: Python is older than the required minimum for this workflow.")
        failures += 1

    occa_path = shutil.which(args.occa) if args.occa == "occa" else str(Path(args.occa))
    print(f"occa_executable={occa_path or 'NOT_FOUND'}")
    if not occa_path:
        print("ERROR: occa is not available on PATH. Activate the OCCA Python environment first.")
        failures += 1
    else:
        try:
            completed = subprocess.run(
                [occa_path, "--version"],
                check=False,
                text=True,
                capture_output=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            print("ERROR: occa --version timed out.")
            failures += 1
        except OSError as exc:
            print(f"ERROR: unable to run occa --version: {exc}")
            failures += 1
        else:
            output = "\n".join(
                part.strip()
                for part in [completed.stdout, completed.stderr]
                if part and part.strip()
            )
            print(f"occa_version_exit_code={completed.returncode}")
            print("occa_version_output_begin")
            print(output)
            print("occa_version_output_end")
            if completed.returncode:
                failures += 1

    print(f"latest_release_check={args.release_url}")
    print(
        "latest_release_note=This site requires Oracle authentication/MFA; compare the installed "
        "occa --version output with the latest wheel listed there before processing customer data."
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
