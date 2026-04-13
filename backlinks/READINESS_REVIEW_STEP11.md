# Step 11 Readiness Review (Manual Weekly Operations)

Date: 2026-04-13
Scope: readiness for real weekly manual use before source automation or messaging integration.

## 1) Readiness verdict

**Verdict: Conditionally ready for real weekly manual operation now (pilot mode).**

Why:
- Core loop exists and is deterministic: prep run -> human review -> finalize.
- Drift-control is in place via explicit review-apply gate.
- Stable `row_id` reduces matching ambiguity.
- Artifacts are date-scoped and auditable.

Condition:
- First 2–4 live weekly runs should be treated as supervised pilot runs with explicit operator sign-off.

## 2) Remaining critical gaps

1. **No true live-source variability tested yet**
   - Current tests are sample-data driven.
   - Need real export shape/quality validation from actual weekly source.

2. **Draft-vs-final output misunderstanding risk**
   - Prep report/alert can differ from final post-review state.
   - Operators must consistently run finalize step.

3. **Runbook enforcement is documentation-only**
   - No hard guardrails prevent skipping finalize/apply.

4. **No formal data quality checks on import values**
   - Minimal validation for malformed domains/URLs and stale dates.

5. **No operational SLA/ownership metadata**
   - Reviewer identity and timestamp are not yet mandatory audit fields.

## 3) Recommended next step

**Recommended next step: real weekly live use (pilot), not Bing automation/cron automation/Telegram yet.**

Rationale:
- System logic is ready for human-operated weekly runs.
- Biggest unknown is real-world data quality and operator behavior, not missing code paths.
- Live manual pilot will reveal practical edge cases before introducing automation complexity.

Decision on alternatives:
- Bing automation: wait until 2–4 successful live manual weeks establish stable expectations.
- Cron automation: wait until finalize discipline is consistently followed manually.
- Telegram messaging: wait until final (post-apply) report/alert trust is established.

## 4) Exact minimum real-world test procedure (next)

### Week 1 pilot test (real run)

1. Export real backlink CSV for `thymemachinecafe.com` (chosen source profile).
2. Save file as `backlinks/imports/inbox/weekly-export.csv`.
3. Run prep flow:

```bash
python backlinks/scripts/run_weekly_backlink_flow.py \
  --source manual \
  --input backlinks/imports/inbox/weekly-export.csv \
  --run-date YYYY-MM-DD \
  --target-domain thymemachinecafe.com
```

4. Open review CSV and complete approvals/overrides:
   - set `decision=approve` row-by-row where appropriate
   - set `approved_status` / `approved_suspicious_flag` / `approved_suspicious_reason` as needed
5. Run finalize dry-run:

```bash
python backlinks/scripts/run_finalize_after_review.py --run-date YYYY-MM-DD --dry-run
```

6. Validate dry-run summary (expected changed rows, no unexpected ambiguous/no-match spikes).
7. Run finalize apply:

```bash
python backlinks/scripts/run_finalize_after_review.py --run-date YYYY-MM-DD
```

8. Confirm final outputs exist and match reviewed intent:
   - `backlinks/reports/YYYY-MM-DD-weekly.md`
   - `backlinks/alerts/YYYY-MM-DD-alert-summary.txt`
9. Manually send/copy alert summary to team channel.
10. Move source CSV to `imports/processed/`.
11. Commit artifacts and record pilot observations (time taken, pain points, errors).

## Exit criteria to proceed beyond pilot

After 2–4 live weekly runs, proceed to Bing automation only if:
- No major drift incidents
- Operator sequence followed without missed finalize steps
- Review/apply ambiguity rate remains low
- Weekly runtime is acceptable operationally
