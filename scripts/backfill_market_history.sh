#!/usr/bin/env sh
set -eu

TO_DATE="${FINMIND_BACKFILL_TO_DATE:-$(date +%Y-%m-%d)}"
FROM_DATE="${FINMIND_BACKFILL_FROM_DATE:-$(date -v-1m +%Y-%m-%d 2>/dev/null || date -d "$TO_DATE -1 month" +%Y-%m-%d)}"

uv run python -m api.platform.ingestion.backfill \
  --preset "${FINMIND_BACKFILL_PRESET:-market-history}" \
  --from-date "$FROM_DATE" \
  --to-date "$TO_DATE"
