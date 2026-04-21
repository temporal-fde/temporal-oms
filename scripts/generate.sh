#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> buf generate"
buf generate

echo "==> fixing p2p imports"
python/.venv/bin/python scripts/fix_p2p_imports.py
