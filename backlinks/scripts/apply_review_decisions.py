#!/usr/bin/env python3
"""Apply approved review decisions back into tracker.csv (Step 11 hardened)."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRACKER = ROOT / "data" / "tracker.csv"
DEFAULT_REVIEWS = ROOT / "reviews"
APPROVE_VALUES = {"approve", "approved", "yes", "y", "1", "true"}


@dataclass
class Counters:
    review_rows: int = 0
    approved_rows: int = 0
    applied_changes: int = 0
    unchanged: int = 0
    skipped_unapproved: int = 0
    skipped_no_match: int = 0
    skipped_ambiguous_match: int = 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Apply approved review decisions into tracker.csv")
    p.add_argument("--run-date", required=True, help="Run date (YYYY-MM-DD)")
    p.add_argument("--review", help="Review CSV override path")
    p.add_argument("--tracker", default=str(DEFAULT_TRACKER), help="Tracker CSV path")
    p.add_argument("--dry-run", action="store_true", help="Preview changes without writing tracker")
    return p.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


def is_approved(review_row: dict[str, str]) -> bool:
    return (review_row.get("decision", "") or "").strip().lower() in APPROVE_VALUES


def choose_value(review_row: dict[str, str], approved_col: str, fallback_col: str) -> str:
    return ((review_row.get(approved_col, "") or "").strip() or (review_row.get(fallback_col, "") or "").strip())


def build_indexes(tracker_rows: list[dict[str, str]]) -> tuple[dict[str, list[int]], dict[tuple[str, str], list[int]]]:
    by_row_id: dict[str, list[int]] = {}
    by_legacy: dict[tuple[str, str], list[int]] = {}
    for i, row in enumerate(tracker_rows):
        rid = (row.get("row_id", "") or "").strip()
        if rid:
            by_row_id.setdefault(rid, []).append(i)
        key = ((row.get("run_date", "") or "").strip(), (row.get("referring_domain", "") or "").strip().lower())
        by_legacy.setdefault(key, []).append(i)
    return by_row_id, by_legacy


def find_match(review_row: dict[str, str], by_row_id: dict[str, list[int]], by_legacy: dict[tuple[str, str], list[int]]) -> list[int]:
    rid = (review_row.get("row_id", "") or "").strip()
    if rid:
        return by_row_id.get(rid, [])
    key = ((review_row.get("run_date", "") or "").strip(), (review_row.get("referring_domain", "") or "").strip().lower())
    return by_legacy.get(key, [])


def main() -> None:
    args = parse_args()
    tracker_path = Path(args.tracker)
    review_path = Path(args.review) if args.review else (DEFAULT_REVIEWS / f"{args.run_date}-classification-review.csv")

    tracker_rows = read_csv(tracker_path)
    tracker_cols = list(tracker_rows[0].keys()) if tracker_rows else []
    review_rows = read_csv(review_path)

    by_row_id, by_legacy = build_indexes(tracker_rows)
    counters = Counters()
    changed_examples: list[str] = []

    for review_row in review_rows:
        counters.review_rows += 1
        if (review_row.get("run_date", "") or "").strip() != args.run_date:
            continue
        if not is_approved(review_row):
            counters.skipped_unapproved += 1
            continue
        counters.approved_rows += 1

        matches = find_match(review_row, by_row_id, by_legacy)
        if len(matches) == 0:
            counters.skipped_no_match += 1
            continue
        if len(matches) > 1:
            counters.skipped_ambiguous_match += 1
            continue

        tracker_row = tracker_rows[matches[0]]
        new_status = choose_value(review_row, "approved_status", "suggested_status")
        new_flag = choose_value(review_row, "approved_suspicious_flag", "suggested_suspicious_flag")
        new_reason = (review_row.get("approved_suspicious_reason", "") or "").strip()

        before = (
            (tracker_row.get("status", "") or "").strip(),
            (tracker_row.get("suspicious_flag", "") or "").strip(),
            (tracker_row.get("suspicious_reason", "") or "").strip(),
        )

        if new_status:
            tracker_row["status"] = new_status
        if new_flag:
            tracker_row["suspicious_flag"] = new_flag
        if new_reason:
            tracker_row["suspicious_reason"] = new_reason

        marker = f"review_applied:{args.run_date}"
        note = (tracker_row.get("notes", "") or "").strip()
        if marker not in note:
            tracker_row["notes"] = f"{note} | {marker}".strip(" |")

        after = (
            (tracker_row.get("status", "") or "").strip(),
            (tracker_row.get("suspicious_flag", "") or "").strip(),
            (tracker_row.get("suspicious_reason", "") or "").strip(),
        )

        if before == after:
            counters.unchanged += 1
            continue

        counters.applied_changes += 1
        domain = (review_row.get("referring_domain", "") or "").strip().lower()
        changed_examples.append(f"- {domain}: status {before[0]} -> {after[0]}, suspicious_flag {before[1]} -> {after[1]}")

    print("=== Review Apply Summary ===")
    print(f"Run date: {args.run_date}")
    print(f"Review rows: {counters.review_rows} | approved: {counters.approved_rows} | applied: {counters.applied_changes}")
    print(f"Skipped -> unapproved: {counters.skipped_unapproved}, no_match: {counters.skipped_no_match}, ambiguous: {counters.skipped_ambiguous_match}")
    if changed_examples:
        print("Changes:")
        for line in changed_examples[:20]:
            print(line)

    if args.dry_run:
        print("Dry-run only: tracker unchanged.")
        return

    if counters.applied_changes > 0:
        write_csv(tracker_path, tracker_rows, tracker_cols)
        print(f"Tracker updated: {tracker_path}")
    else:
        print("No tracker changes written.")


if __name__ == "__main__":
    main()
