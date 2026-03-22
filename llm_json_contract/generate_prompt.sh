#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTRUCTIONS_FILE="${1:-$ROOT_DIR/instructions.md}"
REPORT_FILE="${2:-$ROOT_DIR/daily_report.json}"

if [[ ! -f "$INSTRUCTIONS_FILE" ]]; then
  echo "Missing instructions file: $INSTRUCTIONS_FILE" >&2
  exit 1
fi

if [[ ! -f "$REPORT_FILE" ]]; then
  echo "Missing report file: $REPORT_FILE" >&2
  exit 1
fi

cat <<EOF
You are analyzing a machine-readable daily market snapshot for short-term trading decision support.

Your task:
- Analyze the provided JSON market snapshot.
- Infer current market positioning from breadth, industry leadership, bond/treasury behavior, and sector ETF behavior.
- Focus first on 1-5 day trading opportunities, then on secondary swing opportunities.
- Return strict JSON only.

Follow these instructions exactly:

EOF

cat "$INSTRUCTIONS_FILE"

cat <<EOF

Here is the input JSON to analyze:

\`\`\`json
EOF

cat "$REPORT_FILE"

cat <<EOF
\`\`\`

Return only the final JSON object. Do not include markdown fences. Do not explain your reasoning outside the JSON.
EOF
