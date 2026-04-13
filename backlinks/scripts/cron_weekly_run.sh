#!/usr/bin/env bash
set -euo pipefail

# Step 9: cron-safe local wrapper for weekly backlink run.
# - validates required inputs
# - writes dated logs
# - keeps messaging manual

usage() {
  cat >&2 <<USAGE
Usage:
  backlinks/scripts/cron_weekly_run.sh \
    --source <manual|gsc|bing> \
    --input <csv_path> \
    --target-domain <domain> \
    [--run-date YYYY-MM-DD] \
    [--repo-root /workspace/hello-world]
USAGE
}

SOURCE=""
INPUT=""
TARGET_DOMAIN=""
RUN_DATE="$(date -u +%F)"
REPO_ROOT="/workspace/hello-world"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      SOURCE="${2:-}"; shift 2 ;;
    --input)
      INPUT="${2:-}"; shift 2 ;;
    --target-domain)
      TARGET_DOMAIN="${2:-}"; shift 2 ;;
    --run-date)
      RUN_DATE="${2:-}"; shift 2 ;;
    --repo-root)
      REPO_ROOT="${2:-}"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Error: unknown argument: $1" >&2
      usage
      exit 2 ;;
  esac
done

if [[ -z "$SOURCE" || -z "$INPUT" || -z "$TARGET_DOMAIN" ]]; then
  echo "Error: missing required arguments (--source, --input, --target-domain)." >&2
  usage
  exit 2
fi

if [[ ! -f "$INPUT" ]]; then
  echo "Error: input CSV not found: $INPUT" >&2
  exit 3
fi

if [[ ! -d "$REPO_ROOT" ]]; then
  echo "Error: repo root not found: $REPO_ROOT" >&2
  exit 4
fi

LOG_DIR="$REPO_ROOT/backlinks/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/${RUN_DATE}-weekly-run.log"

{
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] START cron_weekly_run"
  echo "run_date=$RUN_DATE source=$SOURCE input=$INPUT target_domain=$TARGET_DOMAIN"

  cd "$REPO_ROOT"
  python3 backlinks/scripts/run_weekly_backlink_flow.py \
    --source "$SOURCE" \
    --input "$INPUT" \
    --run-date "$RUN_DATE" \
    --target-domain "$TARGET_DOMAIN"

  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] DONE cron_weekly_run"
  echo "Manual step required: review classification CSV, run apply_review_decisions, regenerate report+alert if changes are approved."
} >> "$LOG_FILE" 2>&1

echo "OK: weekly run completed. Log: $LOG_FILE"
