# Reviews

This folder stores classifier outputs for human validation.

File pattern:
- `reviews/YYYY-MM-DD-classification-review.csv`

## Explicit review schema (Step 11)

Generated columns:
- `row_id`
- `run_date`
- `referring_domain`
- `current_status`
- `current_suspicious_flag`
- `classification_label`
- `suggested_status`
- `suggested_suspicious_flag`
- `reasons`
- `decision`
- `approved_status`
- `approved_suspicious_flag`
- `approved_suspicious_reason`
- `notes`

Operator action:
- set `decision=approve` to allow apply step
- optionally set `approved_*` overrides (otherwise suggested values are used)

Important:
- Heuristic labels are suggestions only.
- Human review is mandatory before final tracker state is updated.
