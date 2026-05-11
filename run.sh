#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PIPELINE="src/pipeline/run_pipeline.py"

usage() {
  cat <<'EOF'
Run the textbook ingestion pipeline from the repo root.

With no arguments, runs preprocess -> extract -> normalize -> readable on the
first 10 pages of the sample PDF, skipping Docling, using Gemini Flash.

Examples:
  ./run.sh
  ./run.sh --list-stages
  ./run.sh --all-pages --skip-docling
  ./run.sh --only normalize --provider ollama --model qwen2.5:14b-instruct-q4_K_M
  ./run.sh --from-stage extract --to-stage readable --max-pages 3

All flags are forwarded to src/pipeline/run_pipeline.py.
Set GOOGLE_API_KEY in .env for Gemini normalization.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || "${1:-}" == "help" ]]; then
  usage
  exit 0
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv is required. Install it from https://docs.astral.sh/uv/" >&2
  exit 1
fi

if [[ ! -f "$PIPELINE" ]]; then
  echo "error: missing $PIPELINE" >&2
  exit 1
fi

if [[ $# -eq 0 ]]; then
  set -- \
    --max-pages 10 \
    --skip-docling \
    --provider gemini \
    --model gemini-2.5-flash \
    --batch-size 1
fi

exec uv run python "$PIPELINE" "$@"
