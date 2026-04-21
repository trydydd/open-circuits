#!/bin/bash
set -euo pipefail

# Only run in remote (web/mobile) sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# Set up venv if missing
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  .venv/bin/pip install --quiet --upgrade pip
  .venv/bin/pip install --quiet -r requirements-dev.txt
fi

# Build HTML output so Claude can read output/html/ directly
# --skip-integrity speeds up the build; integrity is verified in CI
.venv/bin/python build/build_html.py --skip-integrity
