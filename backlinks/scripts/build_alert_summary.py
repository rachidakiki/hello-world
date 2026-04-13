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
ALERTS_DIR = ROOT / "alerts"
REVIEWS_DIR = ROOT / "reviews"
TRACKER_PATH = ROOT / "data" / "tracker.csv"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build concise draft alert summary from tracker + review CSV")
    p.add_argument("--run-date", required=True, help="Run date (YYYY-MM-DD)")
    return p.parse_args()


def count_raw_rows(run_date: str) -> int:
    with TRACKER_PATH.open(newline="", encoding="utf-8") as f:
        return sum(1 for row in csv.DictReader(f) if (row.get("run_date", "") or "").strip() == run_date)


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
    raw_rows = count_raw_rows(args.run_date)
    review_counts = load_review_counts(args.run_date)
    normal_count = review_counts["likely_normal"]
    lost_count = review_counts["likely_lost"]
    broken_count = review_counts["likely_broken"]
    suspicious_count = review_counts["likely_suspicious"]
    needs_review_count = review_counts["needs_review"]

    actions = build_actions(lost_count, broken_count, suspicious_count, needs_review_count, normal_count)
    status = overall_status(lost_count, broken_count, suspicious_count, needs_review_count)

    summary = [
        "Backlink Weekly Draft Alert",
        f"Run date: {args.run_date}",
        f"Raw rows imported: {raw_rows}",
        "Suggested classification counts (pre-approval):",
        f"- Normal: {normal_count}",
        f"- Suspicious: {suspicious_count}",
        f"- Lost: {lost_count}",
        f"- Broken: {broken_count}",
        f"- Needs_review: {needs_review_count}",
        "Top action items:",
        f"1) {actions[0]}",
        f"2) {actions[1] if len(actions) > 1 else '—'}",
        f"3) {actions[2] if len(actions) > 2 else '—'}",
        f"Overall draft status: {status}",
    ]

    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ALERTS_DIR / f"{args.run_date}-alert-summary.txt"
    out_text = "\n".join(summary) + "\n"
    out_path.write_text(out_text, encoding="utf-8")

    print(out_text, end="")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
