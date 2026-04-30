#!/bin/bash
set -e

echo "🛑 Tearing down KinD demo environment..."
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

bash scripts/kind/app-down.sh
echo ""
bash scripts/kind/infra-down.sh
echo ""
echo "✅ KinD demo environment removed"
