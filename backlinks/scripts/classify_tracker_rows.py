#!/usr/bin/env python3
"""Heuristic classification for tracker rows with explicit review schema (Step 11)."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRACKER = ROOT / "data" / "tracker.csv"
DEFAULT_REVIEWS_DIR = ROOT / "reviews"

SUSPICIOUS_TLDS = {".xyz", ".top", ".click", ".info", ".buzz", ".work", ".loan"}
SUSPICIOUS_KEYWORDS = {"casino", "viagra", "porn", "adult", "loan", "crypto", "bet", "coupon", "free-seo", "backlink", "directory", "submit"}


def make_row_id(row: dict[str, str]) -> str:
    raw = "|".join([
        (row.get("run_date", "") or "").strip(),
        (row.get("source_name", "") or "").strip(),
        (row.get("referring_domain", "") or "").strip().lower(),
        (row.get("backlink_url", "") or "").strip(),
        (row.get("target_url", "") or "").strip(),
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create a heuristic backlink classification review file.")
    p.add_argument("--tracker", default=str(DEFAULT_TRACKER), help="Path to tracker CSV")
    p.add_argument("--run-date", help="Filter rows by run date (YYYY-MM-DD). Default: latest run_date in tracker")
    p.add_argument("--lost-threshold-days", type=int, default=30, help="Days since last_seen_date to suggest likely_lost")
    p.add_argument(
        "--gsc-lost-threshold-days",
        type=int,
        default=120,
        help="Days since last_seen_date to suggest likely_lost for source_name=gsc_links",
    )
    return p.parse_args()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        if not (row.get("row_id", "") or "").strip():
            row["row_id"] = make_row_id(row)
    return rows


def parse_date(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def is_suspicious_domain(domain: str) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    d = domain.strip().lower()
    if not d:
        return True, ["missing_domain"]
    if any(d.endswith(tld) for tld in SUSPICIOUS_TLDS):
        reasons.append("suspicious_tld")
    for kw in SUSPICIOUS_KEYWORDS:
        if kw in d:
            reasons.append(f"keyword:{kw}")
    if d.count("-") >= 3:
        reasons.append("many_hyphens")
    if re.search(r"\d{4,}", d):
        reasons.append("long_numeric_pattern")
    return (len(reasons) > 0), reasons


def classify_row(
    row: dict[str, str],
    run_date: datetime,
    lost_threshold_days: int,
    gsc_lost_threshold_days: int,
) -> tuple[str, list[str], str, str]:
    reasons: list[str] = []
    status = (row.get("status", "") or "").strip().lower()
    source_name = (row.get("source_name", "") or "").strip().lower()
    domain = (row.get("referring_domain", "") or "").strip().lower()
    last_seen = parse_date(row.get("last_seen_date", ""))
    http_status_raw = (row.get("http_status", "") or "").strip()
    suspicious, suspicious_reasons = is_suspicious_domain(domain)

    if http_status_raw.isdigit() and int(http_status_raw) >= 400:
        return "likely_broken", [f"http_status_{http_status_raw}"], "broken", "false"
    if status == "broken":
        return "likely_broken", ["status_marked_broken"], "broken", "false"
    if status == "lost":
        return "likely_lost", ["status_marked_lost"], "lost", "false"
    if last_seen is None:
        return "needs_review", ["missing_last_seen_date"], "unknown", "false"

    age_days = (run_date - last_seen).days
    stale_threshold = gsc_lost_threshold_days if source_name == "gsc_links" else lost_threshold_days
    if age_days > stale_threshold:
        if source_name == "gsc_links":
            reason = f"stale_last_seen_gsc:{age_days}d>{stale_threshold}d"
        else:
            reason = f"stale_last_seen:{age_days}d>{stale_threshold}d"
        return "likely_lost", [reason], "lost", "false"

    if suspicious:
        reasons.extend(suspicious_reasons)
        return "likely_suspicious", reasons, "suspicious", "true"

    if not (row.get("backlink_url", "") or "").strip() and not (row.get("target_url", "") or "").strip():
        return "needs_review", ["missing_both_urls"], "unknown", "false"

    return "likely_normal", ["no_high_risk_signals"], "active", "false"


def detect_run_date(rows: list[dict[str, str]], override: str | None) -> str:
    if override:
        datetime.strptime(override, "%Y-%m-%d")
        return override
    dates = sorted({(r.get("run_date", "") or "").strip() for r in rows if (r.get("run_date", "") or "").strip()})
    if not dates:
        raise SystemExit("No run_date values found in tracker")
    return dates[-1]


def write_review_file(path: Path, rows: list[dict[str, str]]) -> None:
    columns = [
        "row_id",
        "run_date",
        "referring_domain",
        "current_status",
        "current_suspicious_flag",
        "classification_label",
        "suggested_status",
        "suggested_suspicious_flag",
        "reasons",
        "decision",
        "approved_status",
        "approved_suspicious_flag",
        "approved_suspicious_reason",
        "notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    tracker_path = Path(args.tracker)
    rows = load_rows(tracker_path)
    run_date_str = detect_run_date(rows, args.run_date)
    run_date = datetime.strptime(run_date_str, "%Y-%m-%d")

    selected = [r for r in rows if (r.get("run_date", "") or "").strip() == run_date_str]
    review_rows: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for row in selected:
        label, reasons, suggested_status, suggested_suspicious_flag = classify_row(
            row,
            run_date,
            args.lost_threshold_days,
            args.gsc_lost_threshold_days,
        )
        counts[label] += 1
        review_rows.append(
            {
                "row_id": (row.get("row_id", "") or "").strip() or make_row_id(row),
                "run_date": run_date_str,
                "referring_domain": (row.get("referring_domain", "") or "").strip(),
                "current_status": (row.get("status", "") or "").strip(),
                "current_suspicious_flag": (row.get("suspicious_flag", "") or "").strip(),
                "classification_label": label,
                "suggested_status": suggested_status,
                "suggested_suspicious_flag": suggested_suspicious_flag,
                "reasons": "|".join(reasons),
                "decision": "",
                "approved_status": "",
                "approved_suspicious_flag": "",
                "approved_suspicious_reason": "",
                "notes": "human_review_required",
            }
        )

    out_path = DEFAULT_REVIEWS_DIR / f"{run_date_str}-classification-review.csv"
    write_review_file(out_path, review_rows)

    print(f"Wrote review file: {out_path}")
    for key in ["likely_normal", "likely_suspicious", "likely_lost", "likely_broken", "needs_review"]:
        print(f"- {key}: {counts.get(key, 0)}")


if __name__ == "__main__":
    main()
