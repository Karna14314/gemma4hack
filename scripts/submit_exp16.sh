#!/usr/bin/env bash
# Copy-paste submit for exp16_grader_aligned_36calls.
# Run ONLY after explicit user yes: no PENDING rows, nothing submitted today (UTC), numAllowedNow > 0.
set -euo pipefail

export KAGGLE_API_TOKEN="${KAGGLE_API_TOKEN:-$KAGGLE_KEY}"
KAGGLE_JSON_BACKUP="${HOME}/.kaggle/kaggle.json.bak"
[ -f "${HOME}/.kaggle/kaggle.json" ] && mv "${HOME}/.kaggle/kaggle.json" "${KAGGLE_JSON_BACKUP}"

kaggle competitions submit -c gemma-4-developer-agent \
  -k narisettichaitanya/gemma4-devagent-exp16-grader-aligned-36-calls \
  -v 1 -f submission.zip \
  -m "exp16: exp05 + 36 calls/9m + pytest -p no:anyio + py_compile gate"

[ -f "${KAGGLE_JSON_BACKUP}" ] && mv "${KAGGLE_JSON_BACKUP}" "${HOME}/.kaggle/kaggle.json"
