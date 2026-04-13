#!/usr/bin/env python3
"""Finalize weekly outputs after human review (Step 11).

Runs:
1) apply_review_decisions.py
2) generate_weekly_report.py
3) build_alert_summary.py
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Apply approved review decisions and regenerate final report/alert")
    p.add_argument("--run-date", required=True, help="Run date (YYYY-MM-DD)")
    p.add_argument("--tracker", default=str(ROOT / "data" / "tracker.csv"), help="Tracker CSV path")
    p.add_argument("--review", help="Review CSV override path")
    p.add_argument("--dry-run", action="store_true", help="Run apply step in dry-run mode and stop")
    return p.parse_args()


def run(cmd: list[str], label: str) -> None:
    print(f"[step] {label}")
    subprocess.run(cmd, check=True)


def main() -> None:
    args = parse_args()

    apply_cmd = [
        sys.executable,
        str(SCRIPTS / "apply_review_decisions.py"),
        "--run-date",
        args.run_date,
        "--tracker",
        args.tracker,
    ]
    if args.review:
        apply_cmd += ["--review", args.review]
    if args.dry_run:
        apply_cmd += ["--dry-run"]

    run(apply_cmd, "apply review decisions")

    if args.dry_run:
        print("Finalize dry-run complete (no report/alert regeneration).")
        return

    run([sys.executable, str(SCRIPTS / "generate_weekly_report.py"), args.run_date], "regenerate weekly report")
    run([sys.executable, str(SCRIPTS / "build_alert_summary.py"), "--run-date", args.run_date], "regenerate alert summary")

    print("Finalize complete.")


if __name__ == "__main__":
    main()
