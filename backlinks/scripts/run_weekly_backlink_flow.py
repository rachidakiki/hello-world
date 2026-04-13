#!/usr/bin/env python3
"""One-command weekly prep flow (Step 11 simplified output)."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
DEFAULT_TRACKER = ROOT / "data" / "tracker.csv"
DEFAULT_REVIEWS_DIR = ROOT / "reviews"
DEFAULT_REPORTS_DIR = ROOT / "reports"
DEFAULT_ALERTS_DIR = ROOT / "alerts"

EXIT_STATES = {
    "no_issues": "no issues",
    "review_suspicious": "review suspicious domains",
    "recover_lost": "recover lost links",
    "inspect_broken": "inspect broken links",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run weekly backlink prep flow: import -> classify -> report -> alert")
    p.add_argument("--source", choices=["gsc", "bing", "manual"], required=True, help="Import mapping profile")
    p.add_argument("--input", required=True, help="Path to input CSV export")
    p.add_argument("--run-date", required=True, help="Run date (YYYY-MM-DD)")
    p.add_argument("--target-domain", required=True, help="Target domain")
    p.add_argument("--tracker", default=str(DEFAULT_TRACKER), help="Path to tracker CSV")
    return p.parse_args()


def run_cmd(cmd: list[str], label: str) -> None:
    print(f"[step] {label}")
    subprocess.run(cmd, check=True)


def load_classification_counts(review_path: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    with review_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            label = (row.get("classification_label", "") or "").strip()
            if label:
                counts[label] += 1
    return counts


def decide_exit_state(counts: Counter[str]) -> str:
    if counts.get("likely_broken", 0) > 0:
        return EXIT_STATES["inspect_broken"]
    if counts.get("likely_lost", 0) > 0:
        return EXIT_STATES["recover_lost"]
    if counts.get("likely_suspicious", 0) > 0 or counts.get("needs_review", 0) > 0:
        return EXIT_STATES["review_suspicious"]
    return EXIT_STATES["no_issues"]


def main() -> None:
    args = parse_args()
    datetime.strptime(args.run_date, "%Y-%m-%d")

    run_cmd([
        sys.executable, str(SCRIPTS_DIR / "import_backlinks_csv.py"),
        "--source", args.source,
        "--input", args.input,
        "--run-date", args.run_date,
        "--target-domain", args.target_domain,
        "--tracker", args.tracker,
    ], "import CSV into tracker")

    run_cmd([
        sys.executable, str(SCRIPTS_DIR / "classify_tracker_rows.py"),
        "--tracker", args.tracker,
        "--run-date", args.run_date,
    ], "classify rows and create review CSV")

    run_cmd([sys.executable, str(SCRIPTS_DIR / "generate_weekly_report.py"), args.run_date], "generate draft report")
    run_cmd([sys.executable, str(SCRIPTS_DIR / "build_alert_summary.py"), "--run-date", args.run_date], "generate draft alert")

    review_path = DEFAULT_REVIEWS_DIR / f"{args.run_date}-classification-review.csv"
    counts = load_classification_counts(review_path)
    exit_state = decide_exit_state(counts)

    print("\n=== Weekly Prep Summary ===")
    print(f"Run date: {args.run_date}")
    print(f"Review file: {review_path}")
    print(f"Draft report: {DEFAULT_REPORTS_DIR / f'{args.run_date}-weekly.md'}")
    print(f"Draft alert: {DEFAULT_ALERTS_DIR / f'{args.run_date}-alert-summary.txt'}")
    print(f"Exit state: {exit_state}")
    print("Next: human review -> run_finalize_after_review.py")


if __name__ == "__main__":
    main()
