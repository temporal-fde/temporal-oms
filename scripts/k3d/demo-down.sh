#!/bin/bash
set -e

echo "🛑 Tearing down k3d demo environment..."
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

bash scripts/k3d/app-down.sh
echo ""
bash scripts/k3d/infra-down.sh
echo ""
echo "✅ k3d demo environment removed"
