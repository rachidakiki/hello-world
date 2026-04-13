# Thyme Machine Backlink Monitor (Step 8: Review-Apply Loop (Drift Control))

This is the first **working**, manual-input version of backlink monitoring for `thymemachinecafe.com`.

No scraping and no APIs are used in this step.


## Canonical workflow

Use `backlinks/RUNBOOK_WEEKLY.md` as the primary weekly operator guide.
Older step-by-step sections in this file are retained for history, but the runbook is canonical.

## Files in this system

```text
backlinks/
  README.md
  configs/
    sources.md
    thymemachinecafe.com.yaml
  data/
    tracker.csv
  reports/
    report_template.md
  scripts/
    README.md
```

### What each file is for

- `configs/thymemachinecafe.com.yaml`
  - Site-specific settings: target domain, weekly cadence, allowed data sources, and simple suspicious-domain rules.
- `configs/sources.md`
  - Semrush-free source list and priority guidance.
- `data/tracker.csv`
  - Main tracker (one row per referring domain per run date), updated manually for now.
- `reports/report_template.md`
  - Reusable weekly summary format.
- `scripts/generate_weekly_report.py`
  - Lightweight local script that reads `data/tracker.csv` and generates a dated weekly markdown report.
- `scripts/README.md`
  - Script usage notes and quick commands.


## One-command weekly flow (Step 6)

Run the prep flow in one command (import → classify → draft report → draft alert):

```bash
python backlinks/scripts/run_weekly_backlink_flow.py   --source manual   --input backlinks/imports/inbox/weekly-export.csv   --run-date 2026-04-20   --target-domain thymemachinecafe.com
```

The runner prints a final status summary with one exit state:
- `no issues`
- `review suspicious domains`
- `recover lost links`
- `inspect broken links`

## Tracker columns (quick reference)

`run_date,target_domain,source_name,referring_domain,backlink_url,target_url,first_seen_date,last_seen_date,status,lost_reason,http_status,anchor_text,rel,domain_authority_hint,suspicious_flag,suspicious_reason,notes`

Status values:
- `active`
- `new`
- `lost`
- `broken`
- `suspicious`
- `unknown`

## Included sample rows

`data/tracker.csv` includes:
1. one normal/relevant domain example
2. one suspicious domain example

You can replace these with real data once your first review starts.

## Exact manual weekly workflow

Use this every week (recommended on Monday UTC):

1. **Set review date**
   - Use today’s date as `run_date` (format: `YYYY-MM-DD`).
2. **Collect domain inputs**
   - Export/check from Google Search Console links.
   - Export/check from Bing Webmaster inbound links.
   - Optionally review analytics/log referrers.
3. **Update `data/tracker.csv` manually**
   - Add one row per referring domain seen this week.
   - Fill `source_name`, `referring_domain`, `backlink_url`, `target_url`, and `status`.
   - Mark suspicious items with `suspicious_flag=true` and explain in `suspicious_reason`.
4. **Classify changes**
   - `new`: present this week, not seen before.
   - `lost`: seen before, missing this week.
   - `broken`: backlink page/domain fails (e.g., 404/5xx).
   - `suspicious`: irrelevant or spam-like pattern.
5. **Write this week’s report**
   - Copy `reports/report_template.md` into a dated report file
     (example: `reports/2026-04-13-weekly.md`).
   - Fill counts and short domain lists.
   - Add 3 concrete next actions.
6. **Save and commit**
   - Commit tracker + report updates so history is preserved.



## Import workflow (Step 4)

### 1) Put export CSV into imports inbox
- Save your manual export to `backlinks/imports/inbox/`.
- You can copy the sample format from `backlinks/imports/samples/manual_export_sample.csv`.

### 2) Run the importer

```bash
python backlinks/scripts/import_backlinks_csv.py   --source manual   --input backlinks/imports/samples/manual_export_sample.csv   --run-date 2026-04-20   --target-domain thymemachinecafe.com
```

Supported `--source` profiles:
- `gsc`
- `bing`
- `manual`

The script appends normalized rows to `backlinks/data/tracker.csv`.

### 3) Move processed file
- After import succeeds, move the source CSV to `backlinks/imports/processed/`.

### 4) Run first-pass classification (mandatory pre-review)

```bash
python backlinks/scripts/classify_tracker_rows.py --run-date 2026-04-20
```

### 5) Generate weekly report

```bash
python backlinks/scripts/generate_weekly_report.py 2026-04-20
```

## What still needs human review after import

- Confirm suspicious domains (`suspicious_flag` and `suspicious_reason` are not auto-classified yet).
- Validate whether imported `status` should remain `new`/`active` or be changed to `lost`/`broken` after checks.
- Spot-check domain relevance and link quality.
- Add context in `notes` for outreach, disavow consideration, or monitoring priorities.


## Classification workflow (Step 5)

After import, run the first-pass classifier:

```bash
python backlinks/scripts/classify_tracker_rows.py --run-date 2026-04-20
```

This creates:
- `backlinks/reviews/2026-04-20-classification-review.csv`

### Heuristic rules (deterministic)

The classifier uses conservative rules and produces suggested labels only:
- `likely_broken`
  - `http_status >= 400` OR `status=broken`
- `likely_lost`
  - `status=lost` OR `last_seen_date` older than threshold (default 30 days)
- `likely_suspicious`
  - suspicious TLDs (e.g., `.xyz`, `.top`, `.click`, `.loan`)
  - spammy keywords in domain (e.g., `casino`, `viagra`, `adult`, `backlink`, `directory`, `coupon`)
  - excessive hyphens or long numeric patterns
- `needs_review`
  - missing key values (e.g., missing `last_seen_date`, missing both URLs)
- `likely_normal`
  - no high-risk signals found

### Human review is mandatory

The script writes a **review file with suggestions**, not final truth.
You must manually confirm or override:
- final `status`
- final `suspicious_flag`
- final `suspicious_reason`
- any outreach/disavow notes



## Alert summary workflow (Step 7)

After the weekly report is generated, build a short operator message:

```bash
python backlinks/scripts/build_alert_summary.py --run-date 2026-04-20
```

Output file:
- `backlinks/alerts/2026-04-20-alert-summary.txt`

Message includes:
- run date
- total domains reviewed
- new/lost/broken/suspicious counts
- top action items
- overall status

This text is intentionally short for copy/paste to Telegram or email.
(Actual Telegram/email sending is not wired yet.)



## Review-apply workflow (Step 8)

After human review of `reviews/YYYY-MM-DD-classification-review.csv`, apply approved decisions back to tracker:

```bash
python backlinks/scripts/apply_review_decisions.py   --run-date 2026-04-20   --dry-run
```

If the dry-run summary looks correct, run without `--dry-run`:

```bash
python backlinks/scripts/apply_review_decisions.py   --run-date 2026-04-20
```

Then regenerate report + alert from the updated tracker state:

```bash
python backlinks/scripts/generate_weekly_report.py 2026-04-20
python backlinks/scripts/build_alert_summary.py --run-date 2026-04-20
```

### Safe matching and approval rules

- A review row is applied only when `decision` is explicitly approved (`approve`, `approved`, `yes`, `true`, etc.).
- Matching key is conservative: `(run_date, referring_domain)`.
- If no match or multiple tracker matches are found, the row is skipped.
- Approved values are taken from:
  - `approved_status` (fallback: `suggested_status`)
  - `approved_suspicious_flag` (fallback: `suggested_suspicious_flag`)
  - optional `approved_suspicious_reason`

### Why this removes drift

Before Step 8, review suggestions and tracker/report values could diverge until manual edits were made.
Step 8 applies approved review outcomes back into tracker deterministically, so regenerated reports and alerts reflect the reviewed truth.


## Weekly command (Step 3 automation)

After updating `data/tracker.csv`, generate the weekly summary automatically:

```bash
python backlinks/scripts/generate_weekly_report.py
```

Optional: force a specific run date:

```bash
python backlinks/scripts/generate_weekly_report.py 2026-04-13
```

This creates `backlinks/reports/YYYY-MM-DD-weekly.md` from the tracker snapshot.

## Keep it simple

- Prefer short notes over complex scoring.
- Keep rules human-readable in the YAML config.
- Improve gradually after several weekly runs.


## How this compounds into later automation

- Step 2 gave a stable manual data format (`tracker.csv`).
- Step 3 added deterministic weekly report generation.
- Step 4 added reusable CSV import normalization.
- Step 5 adds conservative pre-classification for faster triage.
- Next steps can add optional alerts/dashboarding without changing the core CSV workflow.



## Finalize runner (Step 11 friction fix)

After approvals are entered in the review CSV, run:

```bash
python backlinks/scripts/run_finalize_after_review.py --run-date YYYY-MM-DD --dry-run
python backlinks/scripts/run_finalize_after_review.py --run-date YYYY-MM-DD
```

This removes manual sequencing mistakes by handling:
- apply approved review decisions
- regenerate final report
- regenerate final alert


## Weekly operator checklist

- [ ] Place this week’s exported CSV into `backlinks/imports/inbox/`.
- [ ] Run `run_weekly_backlink_flow.py` with `--run-date`.
- [ ] Open `backlinks/reviews/YYYY-MM-DD-classification-review.csv` and manually validate labels.
- [ ] Mark approved rows in review CSV using `decision=approve` (and optional `approved_*` fields).
- [ ] Run `apply_review_decisions.py --run-date YYYY-MM-DD --dry-run`, then apply without dry-run.
- [ ] Update tracker fields where needed (`status`, `suspicious_flag`, `suspicious_reason`, `notes`).
- [ ] Open `backlinks/reports/YYYY-MM-DD-weekly.md` and add brief human notes/actions.
- [ ] Build or review `backlinks/alerts/YYYY-MM-DD-alert-summary.txt`.
- [ ] Copy/paste alert summary into Telegram/email channel (manual for now).
- [ ] Move imported file from `imports/inbox/` to `imports/processed/`.
- [ ] Commit tracker + review + report changes.


## Scheduled execution prep (Step 9)

Use the cron-safe wrapper for unattended local runs:

```bash
backlinks/scripts/cron_weekly_run.sh   --source manual   --input /workspace/hello-world/backlinks/imports/inbox/weekly-export.csv   --target-domain thymemachinecafe.com   --run-date 2026-04-20
```

### Logging convention

- Dated logs are written to `backlinks/logs/YYYY-MM-DD-weekly-run.log`.
- Log includes start/end timestamps, run inputs, runner output, and manual follow-up reminder.

### Exact cron usage (example)

Run every Monday at 09:00 UTC:

```cron
0 9 * * 1 cd /workspace/hello-world && backlinks/scripts/cron_weekly_run.sh --source manual --input /workspace/hello-world/backlinks/imports/inbox/weekly-export.csv --target-domain thymemachinecafe.com --run-date $(date -u +\%F)
```

### Human step still required after cron

Cron handles import/classify/draft report/draft alert generation only.
A human must still:
1. review `reviews/YYYY-MM-DD-classification-review.csv`
2. run `apply_review_decisions.py` (`--dry-run` then apply)
3. regenerate report + alert if approved changes were applied
4. manually send/copy alert message (Telegram/email)


## Future cron command (not enabled yet)

When ready, a cron entry could run every Monday at 09:00 UTC:

```bash
0 9 * * 1 cd /workspace/hello-world && /usr/bin/python3 backlinks/scripts/run_weekly_backlink_flow.py --source manual --input backlinks/imports/inbox/weekly-export.csv --run-date $(date -u +\%F) --target-domain thymemachinecafe.com >> backlinks/reports/weekly-run.log 2>&1
```

(Do not enable cron yet in this step.)

### Later messaging handoff
- Cron can run the weekly runner command to generate tracker/review/report/alert files.
- A future notifier script can read `backlinks/alerts/YYYY-MM-DD-alert-summary.txt` and send it to Telegram/email.

