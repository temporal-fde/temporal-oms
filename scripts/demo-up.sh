#!/bin/bash
set -e

# Default to local overlay if not specified
OVERLAY="${OVERLAY:-local}"

echo "🚀 Starting complete demo environment (${OVERLAY} Temporal)..."
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Run setup steps
bash scripts/infra-up.sh
echo ""
OVERLAY="${OVERLAY}" bash scripts/app-deploy.sh
echo ""
echo "🎉 Demo environment ready!"
echo ""
echo "API Access:"
echo "  ./scripts/tunnel.sh  (in another terminal)"
echo "  Then: curl http://localhost:8080/api/actuator/health"
echo "        curl http://localhost:8050/actuator/health"
echo ""
echo "Commands:"
echo "  ./scripts/setup-temporal-namespaces.sh - Create local Temporal namespaces/endpoints"
echo "  ./scripts/demo-down.sh     - Tear down everything"
echo "  ./scripts/app-deploy.sh    - Redeploy apps only"
echo "  ./scripts/status.sh        - Check deployment status"
echo "  ./scripts/tunnel.sh        - Port-forward (run in another terminal)"
echo ""
echo "Use OVERLAY to switch Temporal backend:"
echo "  OVERLAY=cloud ./scripts/demo-up.sh   - Deploy with Temporal Cloud"
echo "  OVERLAY=local ./scripts/demo-up.sh   - Deploy with localhost Temporal (default)"
