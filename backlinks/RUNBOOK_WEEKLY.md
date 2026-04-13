# Canonical Weekly Workflow (Step 11)

Use this as the single source of truth for weekly operations.

## Minimum operator sequence

1. Put weekly source CSV in `backlinks/imports/inbox/`.
2. Run prep flow:

```bash
python backlinks/scripts/run_weekly_backlink_flow.py \
  --source manual \
  --input backlinks/imports/inbox/weekly-export.csv \
  --run-date YYYY-MM-DD \
  --target-domain thymemachinecafe.com
```

3. Open `backlinks/reviews/YYYY-MM-DD-classification-review.csv`.
4. Mark approved rows (`decision=approve`; optional `approved_*` overrides).
5. Finalize:

```bash
python backlinks/scripts/run_finalize_after_review.py --run-date YYYY-MM-DD --dry-run
python backlinks/scripts/run_finalize_after_review.py --run-date YYYY-MM-DD
```

6. Sanity-check final report + alert.
7. Copy alert text to channel (manual).
8. Move source CSV from `imports/inbox/` to `imports/processed/`.
9. Commit tracker/review/report/alert artifacts.

## Why this is canonical

- Reduces ambiguity between draft and final outputs.
- Keeps review-apply gate explicit.
- Minimizes operator context switching across older step docs.
