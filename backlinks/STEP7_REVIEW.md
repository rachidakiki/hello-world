# Step 7 Review Pass (before cron/messaging)

Date: 2026-04-13
Scope: `backlinks/` local workflow only.

## 1) Architecture review

### What is working well
- Clear staged pipeline exists and runs locally:
  1. import CSV into tracker
  2. classify heuristically
  3. generate markdown report
  4. build short alert summary
- All artifacts are file-based and human-reviewable.
- No dependency on Semrush, APIs, or scraping.
- Source mappings are explicit and editable in script.

### Current pain points
- Documentation duplication: `README.md` contains overlapping sections for Step 3/4/5/6/7 and repeats commands.
- `generate_weekly_report.py` derives suspicious counts from tracker flags, while classifier suggests suspicious rows in a separate review file. This can produce mismatch between review and report/alert if human override is not applied.
- Runner prints subprocess command logs intermixed with script outputs, which is usable but noisy.
- Sample/generated artifacts are mixed with templates in the same folders, which can become cluttered over time.

## 2) Simplification recommendations (before Step 8)

1. **Reduce docs to one canonical operator path**
   - Keep one "Weekly Run" section with one command.
   - Move detailed per-script notes to `scripts/README.md`.
2. **Define one source of truth for suspicious/lost/broken counts**
   - Short-term: keep tracker as source of truth and require explicit manual merge from review file before report.
   - Add this as a hard checklist item.
3. **Standardize artifact layout by run date**
   - Keep file names as-is, but enforce one run-date batch convention:
     - `reviews/YYYY-MM-DD-classification-review.csv`
     - `reports/YYYY-MM-DD-weekly.md`
     - `alerts/YYYY-MM-DD-alert-summary.txt`
4. **Trim runner output to one compact summary block**
   - Preserve logs in a file later; keep console output minimal for operators.
5. **Make sample-vs-live distinction explicit**
   - Keep samples in `imports/samples/`; avoid committing ongoing live weekly exports.

## 3) Final weekly operator workflow (concise sequence)

1. Put weekly export CSV into `backlinks/imports/inbox/`.
2. Run one command:

```bash
python backlinks/scripts/run_weekly_backlink_flow.py \
  --source manual \
  --input backlinks/imports/inbox/weekly-export.csv \
  --run-date YYYY-MM-DD \
  --target-domain thymemachinecafe.com
```

3. Open `backlinks/reviews/YYYY-MM-DD-classification-review.csv` and manually confirm/override status + suspicious flags.
4. If any overrides were made, update `backlinks/data/tracker.csv`.
5. Open `backlinks/reports/YYYY-MM-DD-weekly.md`, add short notes/actions.
6. Copy/paste `backlinks/alerts/YYYY-MM-DD-alert-summary.txt` to operator channel (manual for now).
7. Move import file from `imports/inbox/` to `imports/processed/`.
8. Commit tracker + review + report + alert files.

## 4) Exact minimum weekly inputs

Required:
- `--run-date` (YYYY-MM-DD)
- one source CSV export file (at least domain + optional URL columns)
- source profile (`manual`, `gsc`, or `bing`)
- target domain (`thymemachinecafe.com`)

Already in repo (no weekly re-entry needed):
- tracker schema/file (`data/tracker.csv`)
- script mappings and heuristic rules

## 5) Exact weekly outputs

For each run date `YYYY-MM-DD`:
- Tracker append/update: `backlinks/data/tracker.csv`
- Classification review: `backlinks/reviews/YYYY-MM-DD-classification-review.csv`
- Weekly report: `backlinks/reports/YYYY-MM-DD-weekly.md`
- Alert summary: `backlinks/alerts/YYYY-MM-DD-alert-summary.txt`
- Runner terminal summary with exit state:
  - `no issues`
  - `review suspicious domains`
  - `recover lost links`
  - `inspect broken links`

## 6) Step 8 recommendation (after this review)

**Step 8: Add a deterministic "review-apply" script**

Goal:
- Convert reviewed decisions into tracker updates safely and consistently.

Why this is the best next step:
- It resolves the biggest current gap: classifier suggestions and report counts can drift until manual tracker edits are done.
- It keeps the system local/manual-first while reducing operator error.

Suggested Step 8 outputs:
- `scripts/apply_review_decisions.py` to merge reviewed statuses/flags from `reviews/YYYY-MM-DD-classification-review.csv` into tracker rows for the same run date.
- Optional `--dry-run` showing proposed changes before write.
- Small post-apply validation summary (rows changed, unresolved rows).
