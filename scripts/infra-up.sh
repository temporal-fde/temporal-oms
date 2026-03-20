#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "🔧 Setting up infrastructure..."

# Create KinD cluster
if ! kind get clusters 2>/dev/null | grep -q temporal-oms; then
    echo "→ Creating KinD cluster (temporal-oms)..."
    kind create cluster --name temporal-oms
else
    echo "✓ KinD cluster (temporal-oms) already exists"
fi

# Always (re)write the kubeconfig — /tmp can be wiped between sessions
kind get kubeconfig --name temporal-oms > /tmp/kind-config.yaml
export KUBECONFIG=/tmp/kind-config.yaml

# Create namespaces
echo "→ Creating Kubernetes namespaces..."
kubectl create namespace temporal-oms-apps --dry-run=client -o yaml | kubectl apply -f - >/dev/null
kubectl create namespace temporal-oms-processing --dry-run=client -o yaml | kubectl apply -f - >/dev/null

# Install Traefik Ingress Controller
echo "→ Installing Traefik Ingress..."
kubectl apply -f "$PROJECT_DIR/k8s/ingress/traefik-deployment.yaml" >/dev/null

# Wait for Traefik to be ready
kubectl wait --for=condition=ready pod -l app=traefik -n traefik --timeout=60s 2>/dev/null || true

echo "✅ Infrastructure ready!"
echo ""
echo "Next step: ./scripts/app-deploy.sh"
