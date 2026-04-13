#!/usr/bin/env python3
"""Step 7: build short operator alert summaries from weekly reports.

Local-only output intended for copy/paste into Telegram/email/plain text.
No network sending in this step.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
ALERTS_DIR = ROOT / "alerts"
REVIEWS_DIR = ROOT / "reviews"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build concise alert summary from weekly markdown report")
    p.add_argument("--run-date", required=True, help="Run date (YYYY-MM-DD)")
    p.add_argument("--report", help="Optional report file path override")
    return p.parse_args()


def parse_count(lines: list[str], label: str) -> int:
    prefix = f"- {label}:"
    for line in lines:
        s = line.strip()
        if s.startswith(prefix):
            value = s.split(":", 1)[1].strip()
            if value.isdigit():
                return int(value)
    return 0


def load_review_counts(run_date: str) -> dict[str, int]:
    counts = {
        "likely_normal": 0,
        "likely_lost": 0,
        "likely_broken": 0,
        "likely_suspicious": 0,
        "needs_review": 0,
    }
    review_path = REVIEWS_DIR / f"{run_date}-classification-review.csv"
    if not review_path.exists():
        return counts
    with review_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            label = (row.get("classification_label", "") or "").strip()
            if label in counts:
                counts[label] += 1
    return counts


def build_actions(lost_count: int, broken_count: int, suspicious_count: int, needs_review_count: int, normal_count: int) -> list[str]:
    actions: list[str] = []
    if broken_count > 0:
        actions.append("Inspect broken links and confirm HTTP errors")
    if lost_count > 0:
        actions.append("Recover lost links (reach out or re-check source pages)")
    if suspicious_count > 0:
        actions.append("Review suspicious domains and decide keep/watch/disavow")
    if needs_review_count > 0:
        actions.append("Resolve rows marked needs_review before approval")
    if normal_count > 0:
        actions.append("Spot-check likely_normal rows and approve in batches")
    if not actions:
        actions.append("No urgent actions — continue weekly monitoring")
    return actions[:3]


def overall_status(lost_count: int, broken_count: int, suspicious_count: int, needs_review_count: int) -> str:
    if broken_count > 0:
        return "INSPECT BROKEN LINKS"
    if lost_count > 0:
        return "RECOVER LOST LINKS"
    if needs_review_count > 0:
        return "COMPLETE REVIEW QUEUE"
    if suspicious_count > 0:
        return "REVIEW SUSPICIOUS DOMAINS"
    return "NO ISSUES"


def main() -> None:
    args = parse_args()
    report_path = Path(args.report) if args.report else (REPORTS_DIR / f"{args.run_date}-weekly.md")
    lines = report_path.read_text(encoding="utf-8").splitlines()

    total = parse_count(lines, "Total domains")
    raw_rows = parse_count(lines, "Raw imported rows")
    review_counts = load_review_counts(args.run_date)
    normal_count = review_counts["likely_normal"]
    lost_count = review_counts["likely_lost"]
    broken_count = review_counts["likely_broken"]
    suspicious_count = review_counts["likely_suspicious"]
    needs_review_count = review_counts["needs_review"]

    actions = build_actions(lost_count, broken_count, suspicious_count, needs_review_count, normal_count)
    status = overall_status(lost_count, broken_count, suspicious_count, needs_review_count)

    summary = [
        f"Backlink Weekly Alert ({args.run_date})",
        f"Reviewed: {total} domains",
        f"Raw import rows: {raw_rows}",
        (
            "Suggested counts (pre-approval) → "
            f"Normal: {normal_count} | Lost: {lost_count} | Broken: {broken_count} | "
            f"Suspicious: {suspicious_count} | Needs review: {needs_review_count}"
        ),
        "Top actions:",
        f"1) {actions[0]}",
        f"2) {actions[1] if len(actions) > 1 else '—'}",
        f"3) {actions[2] if len(actions) > 2 else '—'}",
        f"Overall status: {status}",
    ]

    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ALERTS_DIR / f"{args.run_date}-alert-summary.txt"
    out_text = "\n".join(summary) + "\n"
    out_path.write_text(out_text, encoding="utf-8")

    print(out_text, end="")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
