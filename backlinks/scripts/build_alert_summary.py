#!/usr/bin/env python3
"""Step 7: build short operator alert summaries from weekly reports.

Local-only output intended for copy/paste into Telegram/email/plain text.
No network sending in this step.
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
ALERTS_DIR = ROOT / "alerts"


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


def build_actions(new_count: int, lost_count: int, broken_count: int, suspicious_count: int) -> list[str]:
    actions: list[str] = []
    if broken_count > 0:
        actions.append("Inspect broken links and confirm HTTP errors")
    if lost_count > 0:
        actions.append("Recover lost links (reach out or re-check source pages)")
    if suspicious_count > 0:
        actions.append("Review suspicious domains and decide keep/watch/disavow")
    if new_count > 0:
        actions.append("Validate new domains for quality and relevance")
    if not actions:
        actions.append("No urgent actions — continue weekly monitoring")
    return actions[:3]


def overall_status(lost_count: int, broken_count: int, suspicious_count: int) -> str:
    if broken_count > 0:
        return "INSPECT BROKEN LINKS"
    if lost_count > 0:
        return "RECOVER LOST LINKS"
    if suspicious_count > 0:
        return "REVIEW SUSPICIOUS DOMAINS"
    return "NO ISSUES"


def main() -> None:
    args = parse_args()
    report_path = Path(args.report) if args.report else (REPORTS_DIR / f"{args.run_date}-weekly.md")
    lines = report_path.read_text(encoding="utf-8").splitlines()

    total = parse_count(lines, "Total domains")
    new_count = parse_count(lines, "New domains")
    lost_count = parse_count(lines, "Lost domains")
    broken_count = parse_count(lines, "Broken domains")
    suspicious_count = parse_count(lines, "Suspicious domains")

    actions = build_actions(new_count, lost_count, broken_count, suspicious_count)
    status = overall_status(lost_count, broken_count, suspicious_count)

    summary = [
        f"Backlink Weekly Alert ({args.run_date})",
        f"Reviewed: {total} domains",
        f"Counts → New: {new_count} | Lost: {lost_count} | Broken: {broken_count} | Suspicious: {suspicious_count}",
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
