#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> buf generate"
buf generate

echo "==> generating converter registry"
python/.venv/bin/python scripts/gen_converter_registry.py

echo "==> fixing p2p imports"
python/.venv/bin/python scripts/fix_p2p_imports.py

echo "==> trimming changed generated Java whitespace"
git diff --name-only -- java/generated/src/main/java | while IFS= read -r file; do
  case "$file" in
    *.java) [ -f "$file" ] && perl -pi -e 's/[ \t]+$//' "$file" ;;
  esac
done
