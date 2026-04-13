#!/usr/bin/env python3
"""Import manually exported backlink CSV files into tracker.csv.

Step 11 update:
- adds stable row_id for each tracker row
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRACKER = ROOT / "data" / "tracker.csv"

TRACKER_COLUMNS = [
    "row_id",
    "run_date",
    "target_domain",
    "source_name",
    "referring_domain",
    "backlink_url",
    "target_url",
    "first_seen_date",
    "last_seen_date",
    "status",
    "lost_reason",
    "http_status",
    "anchor_text",
    "rel",
    "domain_authority_hint",
    "suspicious_flag",
    "suspicious_reason",
    "notes",
]

SOURCE_MAPPINGS = {
    "gsc": {
        "source_name": "gsc_links",
        "referring_domain": ["linking site", "source_domain", "domain", "referring_domain"],
        "backlink_url": ["linking page", "source_url", "backlink_url", "linking_url"],
        "target_url": ["target page", "target_url", "your_page"],
        "anchor_text": ["anchor text", "anchor", "top linked text"],
    },
    "bing": {
        "source_name": "bing_webmaster",
        "referring_domain": ["source_domain", "domain", "referring_domain"],
        "backlink_url": ["source_url", "backlink_url", "linking_url"],
        "target_url": ["target_url", "target page", "your_page"],
        "anchor_text": ["anchor_text", "anchor", "link_text"],
    },
    "manual": {
        "source_name": "manual_export",
        "referring_domain": ["source_domain", "domain", "referring_domain"],
        "backlink_url": ["source_url", "backlink_url", "linking_url"],
        "target_url": ["target_url", "target page", "your_page"],
        "anchor_text": ["anchor_text", "anchor", "link_text"],
    },
}


def make_row_id(run_date: str, source_name: str, referring_domain: str, backlink_url: str, target_url: str) -> str:
    raw = "|".join([run_date, source_name, referring_domain.lower().strip(), backlink_url.strip(), target_url.strip()])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import manual backlink CSV into tracker format.")
    parser.add_argument("--source", choices=sorted(SOURCE_MAPPINGS.keys()), required=True, help="Import mapping profile")
    parser.add_argument("--input", required=True, help="Path to source CSV")
    parser.add_argument("--run-date", required=True, help="Run date (YYYY-MM-DD)")
    parser.add_argument("--target-domain", required=True, help="Target domain, e.g. thymemachinecafe.com")
    parser.add_argument("--tracker", default=str(DEFAULT_TRACKER), help="Path to tracker.csv")
    return parser.parse_args()


def norm_header(name: str) -> str:
    return name.strip().lower()


def pick_value(row: dict[str, str], candidates: list[str]) -> str:
    for key in candidates:
        if key in row and row[key].strip():
            return row[key].strip()
    return ""


def ensure_tracker(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TRACKER_COLUMNS)
        writer.writeheader()


def load_tracker(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normalize_tracker_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        if not row.get("row_id", "").strip():
            row["row_id"] = make_row_id(
                row.get("run_date", "").strip(),
                row.get("source_name", "").strip(),
                row.get("referring_domain", "").strip(),
                row.get("backlink_url", "").strip(),
                row.get("target_url", "").strip(),
            )
        out.append(row)
    return out


def rewrite_tracker(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TRACKER_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in TRACKER_COLUMNS})


def domain_seen_map(tracker_rows: list[dict[str, str]]) -> dict[str, str]:
    seen: dict[str, str] = {}
    for row in tracker_rows:
        domain = row.get("referring_domain", "").strip().lower()
        first_seen = row.get("first_seen_date", "").strip()
        if not domain:
            continue
        if domain not in seen or (first_seen and first_seen < seen[domain]):
            seen[domain] = first_seen or row.get("run_date", "").strip()
    return seen


def read_source_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [{norm_header(k): (v or "") for k, v in raw.items()} for raw in reader]


def main() -> None:
    args = parse_args()
    datetime.strptime(args.run_date, "%Y-%m-%d")

    mapping = SOURCE_MAPPINGS[args.source]
    source_path = Path(args.input)
    tracker_path = Path(args.tracker)

    ensure_tracker(tracker_path)
    tracker_rows = normalize_tracker_rows(load_tracker(tracker_path))
    rewrite_tracker(tracker_path, tracker_rows)
    seen_domains = domain_seen_map(tracker_rows)

    imported = 0
    skipped = 0
    written_keys: set[tuple[str, str]] = set()

    source_rows = read_source_rows(source_path)
    with tracker_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TRACKER_COLUMNS)

        for row in source_rows:
            referring_domain = pick_value(row, mapping["referring_domain"]).lower()
            backlink_url = pick_value(row, mapping["backlink_url"])
            target_url = pick_value(row, mapping["target_url"])
            anchor_text = pick_value(row, mapping["anchor_text"])

            if not referring_domain:
                skipped += 1
                continue

            dedupe_key = (referring_domain, backlink_url)
            if dedupe_key in written_keys:
                skipped += 1
                continue
            written_keys.add(dedupe_key)

            existing_first_seen = seen_domains.get(referring_domain)
            is_new = existing_first_seen is None
            first_seen_date = args.run_date if is_new else existing_first_seen
            source_name = mapping["source_name"]

            tracker_row = {
                "row_id": make_row_id(args.run_date, source_name, referring_domain, backlink_url, target_url),
                "run_date": args.run_date,
                "target_domain": args.target_domain,
                "source_name": source_name,
                "referring_domain": referring_domain,
                "backlink_url": backlink_url,
                "target_url": target_url,
                "first_seen_date": first_seen_date,
                "last_seen_date": args.run_date,
                "status": "new" if is_new else "active",
                "lost_reason": "",
                "http_status": "",
                "anchor_text": anchor_text,
                "rel": "",
                "domain_authority_hint": "",
                "suspicious_flag": "false",
                "suspicious_reason": "",
                "notes": f"imported_from:{source_path.name}",
            }
            writer.writerow(tracker_row)
            imported += 1

    print(f"Imported rows: {imported}")
    print(f"Skipped rows: {skipped}")
    print(f"Tracker updated: {tracker_path}")


if __name__ == "__main__":
    main()
