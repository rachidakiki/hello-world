# Step 10 Manual Dry Run (Realistic Operator Simulation)

Date executed: 2026-04-13
Simulated run date: 2026-04-27
Environment: temporary local copy of `backlinks/` at `/tmp/thyme-dryrun` to avoid altering repo state.

## 1) Exact manual test procedure used

1. Copy current `backlinks/` system to a temp sandbox.
2. Place weekly CSV in `imports/inbox/weekly-export.csv`.
3. Run one-command prep flow:

```bash
python backlinks/scripts/run_weekly_backlink_flow.py \
  --source manual \
  --input /tmp/thyme-dryrun/backlinks/imports/inbox/weekly-export.csv \
  --run-date 2026-04-27 \
  --target-domain thymemachinecafe.com
```

4. Open `reviews/2026-04-27-classification-review.csv` and add reviewer approvals:
   - `decision`
   - optional `approved_status`
   - optional `approved_suspicious_flag`
   - optional `approved_suspicious_reason`
5. Run review-apply dry-run.
6. Run review-apply for real.
7. Regenerate weekly report and alert summary.
8. Verify final artifacts match reviewed decisions.

## 2) Every manual operator step currently required

1. Prepare weekly export CSV and place it in inbox.
2. Choose source profile (`manual`, `gsc`, `bing`) and run date.
3. Run prep flow command.
4. Open review CSV and manually approve/override decisions.
5. Run `apply_review_decisions.py --dry-run` and validate output.
6. Run `apply_review_decisions.py` (write mode).
7. Re-run report + alert generation.
8. Read report and alert for reasonableness.
9. Copy/paste alert to team channel (still manual).
10. Move input CSV to `imports/processed/` and commit artifacts.

## 3) Friction analysis (easy / hard / noisy / missing)

## Easy
- Running the prep flow command is straightforward.
- Output files are predictable by run-date.
- Review-apply dry-run gives clear change preview and skip counts.

## Hard / ambiguous
- **Approval schema is implicit**: operator must know to add `decision` and `approved_*` columns in review CSV.
- **Potential matching ambiguity**: apply step matches `(run_date, referring_domain)` only; duplicate domains in one run would be skipped as ambiguous.
- **Two-phase report truth**: draft report/alert from prep flow may disagree with classifier until review-apply + regeneration is done.

## Noisy
- Prep runner prints subprocess command logs and child output together, making operator logs dense.
- README now contains overlapping step sections; finding canonical sequence takes effort.

## Missing inputs / missing information
- No dedicated reviewer identity field (`reviewed_by`) in review CSV for audit.
- No explicit per-row review timestamp.
- No single command for "post-review finalize" (apply + regenerate report + regenerate alert).

## 4) Observed consistency issue from dry run

In prep flow, classifier flagged one suspicious domain, but draft alert showed suspicious count `0`.
After review-apply and regeneration, suspicious count became `1` and status aligned.

Conclusion: current workflow is correct but requires strict operator discipline to avoid drift.

## 5) Steps worth automating first (highest ROI)

1. **Post-review finalize runner (highest ROI)**
   - Single command: apply approved decisions -> regenerate report -> regenerate alert.
2. **Review CSV schema hardening**
   - Emit optional approval columns by default during classification (empty placeholders).
3. **Stable row matching key**
   - Add deterministic row ID (e.g., hash of run_date+source+domain+backlink_url) to reduce ambiguous matches.
4. **Operator logging cleanup**
   - Keep concise console summary; stream verbose logs to file.
5. **Canonical workflow docs cleanup**
   - One authoritative weekly sequence page + remove duplication.

## 6) Practical operator checklist (for live weekly use)

- [ ] Put weekly CSV in `imports/inbox/`.
- [ ] Run prep flow (`run_weekly_backlink_flow.py`).
- [ ] Review `reviews/YYYY-MM-DD-classification-review.csv`.
- [ ] Add `decision=approve` (+ optional `approved_*` overrides).
- [ ] Run `apply_review_decisions.py --run-date YYYY-MM-DD --dry-run`.
- [ ] If dry-run looks correct, run apply without `--dry-run`.
- [ ] Regenerate report + alert for same run date.
- [ ] Sanity check suspicious/lost/broken counts in final report/alert.
- [ ] Copy alert text to team channel (manual).
- [ ] Move input CSV to `imports/processed/`.
- [ ] Commit tracker/review/report/alert artifacts.
