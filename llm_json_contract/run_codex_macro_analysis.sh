#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
OUTPUT_FILE="$ROOT_DIR/macro_analysis_${TIMESTAMP}.json"
SCHEMA_FILE="$ROOT_DIR/report_schema.json"

cd "$ROOT_DIR"
codex exec --output-schema "$SCHEMA_FILE" -o "$OUTPUT_FILE" "$(bash generate_prompt.sh)" --skip-git-repo-check -c 'reasoning_effort="xhigh"'

echo
echo "Saved Codex output to: $OUTPUT_FILE"
