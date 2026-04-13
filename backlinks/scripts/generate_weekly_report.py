#!/usr/bin/env python3
"""Generate a simple weekly backlink report from data/tracker.csv.

Step 3 scope:
- Local CSV input only
- No scraping
- No external APIs
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKER_PATH = ROOT / "data" / "tracker.csv"
REVIEWS_DIR = ROOT / "reviews"
REPORTS_DIR = ROOT / "reports"


def parse_args() -> str | None:
    """Return optional run_date override (YYYY-MM-DD)."""
    if len(sys.argv) == 1:
        return None
    if len(sys.argv) == 2:
        return sys.argv[1]
    raise SystemExit("Usage: python backlinks/scripts/generate_weekly_report.py [YYYY-MM-DD]")


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def select_run_date(rows: list[dict[str, str]], override: str | None) -> str:
    if override:
        # Validate format early for deterministic behavior.
        datetime.strptime(override, "%Y-%m-%d")
        return override

    run_dates = sorted({row.get("run_date", "").strip() for row in rows if row.get("run_date", "").strip()})
    if not run_dates:
        raise SystemExit("No run_date values found in tracker.csv")
    return run_dates[-1]


def boolish(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def load_review_counts(run_date: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    review_path = REVIEWS_DIR / f"{run_date}-classification-review.csv"
    if not review_path.exists():
        return counts
    with review_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            label = (row.get("classification_label", "") or "").strip()
            if label:
                counts[label] += 1
    return counts


def make_report(rows_for_date: list[dict[str, str]], run_date: str, review_counts: Counter[str]) -> str:
    domains = sorted({r.get("referring_domain", "").strip() for r in rows_for_date if r.get("referring_domain", "").strip()})
    total_domains = len(domains)

    by_status = Counter((r.get("status", "").strip().lower() or "unknown") for r in rows_for_date)

    suspicious_rows = [
        r for r in rows_for_date if boolish(r.get("suspicious_flag", "")) or r.get("status", "").strip().lower() == "suspicious"
    ]

    sources = sorted({r.get("source_name", "").strip() for r in rows_for_date if r.get("source_name", "").strip()})
    target_domain = rows_for_date[0].get("target_domain", "") if rows_for_date else ""

    lines = [
        f"# Backlink Weekly Summary — {run_date}",
        "",
        "## Run Info",
        f"- Target domain: {target_domain}",
        f"- Run date: {run_date}",
        f"- Sources in tracker snapshot: {', '.join(sources) if sources else 'n/a'}",
        "",
        "## Counts (Raw import snapshot from tracker)",
        f"- Raw imported rows: {len(rows_for_date)}",
        f"- Total domains: {total_domains}",
        f"- Tracker new domains: {by_status.get('new', 0)}",
        f"- Tracker lost domains: {by_status.get('lost', 0)}",
        f"- Tracker broken domains: {by_status.get('broken', 0)}",
        f"- Tracker suspicious domains: {len({r.get('referring_domain', '').strip() for r in suspicious_rows if r.get('referring_domain', '').strip()})}",
        "",
        "## Counts (Suggested classification from review CSV, pre-approval)",
        f"- Suggested likely_normal: {review_counts.get('likely_normal', 0)}",
        f"- Suggested likely_lost: {review_counts.get('likely_lost', 0)}",
        f"- Suggested likely_broken: {review_counts.get('likely_broken', 0)}",
        f"- Suggested likely_suspicious: {review_counts.get('likely_suspicious', 0)}",
        f"- Suggested needs_review: {review_counts.get('needs_review', 0)}",
        "",
        "## Domain Details",
    ]

    if not rows_for_date:
        lines.append("- No rows found for this run date.")
    else:
        for row in sorted(rows_for_date, key=lambda r: r.get("referring_domain", "")):
            domain = row.get("referring_domain", "").strip() or "(missing-domain)"
            status = row.get("status", "").strip() or "unknown"
            suspicious_flag = row.get("suspicious_flag", "").strip() or "false"
            suspicious_reason = row.get("suspicious_reason", "").strip()
            suffix = f"; suspicious_reason={suspicious_reason}" if suspicious_reason else ""
            lines.append(f"- {domain} — status={status}; suspicious_flag={suspicious_flag}{suffix}")

    lines.extend([
        "",
        "## Notes",
        "- Raw tracker counts are immediate import snapshot metrics.",
        "- Suggested counts are pulled from reviews/YYYY-MM-DD-classification-review.csv and are pre-approval.",
        "- Final approved counts only become authoritative after review decisions are applied to tracker.",
        "- No scraping or external API calls are used in Step 3.",
    ])

    return "\n".join(lines) + "\n"


def main() -> None:
    run_date_override = parse_args()
    rows = load_rows(TRACKER_PATH)
    run_date = select_run_date(rows, run_date_override)
    rows_for_date = [r for r in rows if r.get("run_date", "").strip() == run_date]
    review_counts = load_review_counts(run_date)

    report_text = make_report(rows_for_date, run_date, review_counts)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"{run_date}-weekly.md"
    output_path.write_text(report_text, encoding="utf-8")

    print(f"Wrote report: {output_path}")


if __name__ == "__main__":
    main()
