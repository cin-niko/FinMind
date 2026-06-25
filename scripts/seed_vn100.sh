#!/usr/bin/env sh
set -eu

CSV_PATH="${FINMIND_VN100_CSV:-data/seed/vn100.csv}"

uv run python -m api.platform.ingestion.seed "$CSV_PATH"
