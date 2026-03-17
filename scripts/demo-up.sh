#!/bin/bash
set -e

echo "🚀 Starting complete demo environment..."
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Run setup steps
bash scripts/infra-up.sh
echo ""
bash scripts/app-deploy.sh
echo ""
echo "🎉 Demo environment ready!"
echo ""
echo "API Access:"
echo "  ./scripts/tunnel.sh  (in another terminal)"
echo "  Then: curl http://localhost:8080/api/actuator/health"
echo ""
echo "Commands:"
echo "  ./scripts/demo-down.sh     - Tear down everything"
echo "  ./scripts/app-deploy.sh    - Redeploy apps only"
echo "  ./scripts/status.sh        - Check deployment status"
echo "  ./scripts/tunnel.sh        - Port-forward (run in another terminal)"
