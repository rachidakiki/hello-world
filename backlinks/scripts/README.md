# Scripts

## Canonical weekly usage

Follow `backlinks/RUNBOOK_WEEKLY.md` for the canonical sequence.

## `run_weekly_backlink_flow.py`

Prep runner (draft artifacts):
1. import
2. classify
3. draft report
4. draft alert

Truth model for draft artifacts:
- Draft report and alert include **raw import snapshot counts** from `tracker.csv`.
- They also include **suggested classification counts** from `reviews/YYYY-MM-DD-classification-review.csv` (pre-approval).
- Final approved truth is only established after review decisions are applied back to tracker.

## `run_finalize_after_review.py`

Finalize runner (after human review approvals):
1. apply approved decisions to tracker
2. regenerate final report
3. regenerate final alert

Dry run:

```bash
python backlinks/scripts/run_finalize_after_review.py --run-date YYYY-MM-DD --dry-run
```

Apply + regenerate:

```bash
python backlinks/scripts/run_finalize_after_review.py --run-date YYYY-MM-DD
```

## `apply_review_decisions.py`

Conservative review merge:
- requires explicit `decision=approve`
- prefers `row_id` exact match
- falls back to `(run_date, referring_domain)`
- skips ambiguous/no-match rows with summary

## `classify_tracker_rows.py`

Writes explicit review schema (including `row_id` + approval fields).

## `import_backlinks_csv.py`

Imports local CSV rows and writes stable `row_id` to tracker.
