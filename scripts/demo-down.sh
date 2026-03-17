#!/bin/bash
set -e

echo "🛑 Tearing down demo environment..."
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

bash scripts/app-down.sh
echo ""
bash scripts/infra-down.sh
echo ""
echo "✅ Demo environment removed"
