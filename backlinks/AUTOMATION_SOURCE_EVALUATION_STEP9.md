# Automated Backlink Source Evaluation (Step 9 Planning)

Date: 2026-04-13
Scope: choose fully automated (no Semrush) sources and design next architecture.

## 1) Source options ranked for full automation

Scoring dimensions:
- Practicality: setup effort + ops burden
- Reliability: backlink coverage/consistency
- Automation value: API maturity + machine-readability

### Rank 1 — Ahrefs API v3 / Ahrefs Connect (paid)
- Practicality: **High** (good docs, mature ecosystem)
- Reliability: **High** (large proprietary backlink index)
- Automation value: **High**
- Notes:
  - API v2 was discontinued (Nov 1, 2025); use API v3/Connect.
  - Best choice when quality and trend continuity matter most.

### Rank 2 — DataForSEO Backlinks API (paid)
- Practicality: **High**
- Reliability: **Medium-High**
- Automation value: **High**
- Notes:
  - Real-time endpoints and explicit pricing model.
  - Strong API-first choice if cost model and latency fit.

### Rank 3 — Bing Webmaster API (free, first-party Bing view)
- Practicality: **High**
- Reliability: **Medium** (engine-specific index; narrower than commercial link indexes)
- Automation value: **Medium-High**
- Notes:
  - Good foundational feed with no extra data vendor.
  - Includes link-related APIs, but coverage depends on Bing discovery.

### Rank 4 — Majestic API (paid)
- Practicality: **Medium**
- Reliability: **Medium-High**
- Automation value: **Medium-High**
- Notes:
  - Longstanding link index provider and API support.
  - Viable alternative if already in stack.

### Not suitable as primary backlink source
- Google Search Console API for backlinks: **not suitable**
  - API reference exposes Search Analytics/Sitemaps/Sites/URL Inspection, but not backlink link-list endpoints.
- Referral analytics/log data (GA4/Cloudflare/server logs): **supplementary only**
  - Useful for impact/traffic validation, not backlink corpus truth.

## 2) Recommended source of truth

### Primary recommendation
Use **Ahrefs API v3/Connect** as primary backlink source of truth for automated weekly ingest.

### Secondary validation source
Use **Bing Webmaster API** as a corroboration feed (cross-check major adds/losses and reduce provider blind spots).

### If budget-constrained fallback
Use **Bing Webmaster API only** as initial auto source, with explicit expectation of lower backlink coverage.

## 3) Authentication requirements

## Ahrefs API v3/Connect
- Vendor API credentials/token (per Ahrefs account/integration model)
- Secret storage for token (env var/secret manager)

## DataForSEO
- API credentials + paid subscription activation (minimum monthly commitment)
- Secret storage for credentials

## Bing Webmaster API
- Site verified in Bing Webmaster Tools
- Either:
  - OAuth 2.0 client credentials + token flow, or
  - Bing Webmaster API key

## Supplementary telemetry (optional)
- GA4 Data API: service account + property access
- Cloudflare GraphQL Analytics: API token scoped for analytics read

## 4) How current system should evolve (manual import -> auto ingest)

Preserve existing tracker/report architecture; replace manual input with adapters.

### Phase A: Ingestion adapters (new)
- `ingest_ahrefs.py` (or `ingest_bing.py`) fetches weekly backlink snapshot via API.
- Write raw pulls to `backlinks/raw/YYYY-MM-DD/<source>.json` for auditability.
- Normalize raw records into current tracker schema fields.

### Phase B: Deterministic merge (replace CSV import dependency)
- Merge normalized rows into `data/tracker.csv` with idempotent logic.
- Keep `run_date` snapshots and status transitions (`new/lost/broken/suspicious`).

### Phase C: Keep existing downstream pipeline
- Reuse current components:
  - classifier
  - review CSV
  - review-apply
  - report generator
  - alert summary
- This keeps human approval and drift-control intact.

### Phase D: Weekly scheduler handoff
- Cron wrapper calls auto-ingest instead of manual CSV import.
- Messaging remains manual until later step.

## 5) Safety and modularity rules for the automated version

- Source adapters must be isolated modules (one script per provider).
- Keep raw payload snapshots for traceability.
- Never overwrite tracker rows without run-date scoping.
- Require deterministic transforms and explicit schema mapping.
- Keep review-apply gate as mandatory for final status corrections.

## References (official docs)
- Ahrefs developer docs: https://docs.ahrefs.com
- Ahrefs Connect (built on API v3): https://docs.ahrefs.com/docs/connect
- Bing Webmaster API overview: https://learn.microsoft.com/en-us/bingwebmaster/
- Google Search Console API reference index: https://developers.google.com/webmaster-tools/v1/api_reference_index
- DataForSEO Backlinks overview: https://docs.dataforseo.com/v3/backlinks-overview/
- Majestic API command overview: https://developer-support.majestic.com/api/commands/
