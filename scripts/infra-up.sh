#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "🔧 Setting up infrastructure..."

# Start Minikube
if ! minikube status &>/dev/null; then
    echo "→ Starting Minikube (4GB RAM, 4 CPUs)..."
    minikube start --memory 4096 --cpus 4
else
    echo "✓ Minikube already running"
fi

# Create namespaces
echo "→ Creating Kubernetes namespaces..."
kubectl create namespace temporal-oms-apps --dry-run=client -o yaml | kubectl apply -f - >/dev/null
kubectl create namespace temporal-oms-processing --dry-run=client -o yaml | kubectl apply -f - >/dev/null

# Create base secrets (empty for local, will be overridden by app-deploy)
echo "→ Creating secrets..."
kubectl create secret generic temporal-secrets -n temporal-oms-apps --from-literal=temporal-secret.yaml="" --dry-run=client -o yaml | kubectl apply -f - >/dev/null
kubectl create secret generic temporal-secrets -n temporal-oms-processing --from-literal=temporal-secret.yaml="" --dry-run=client -o yaml | kubectl apply -f - >/dev/null

# Install Traefik Ingress Controller
echo "→ Installing Traefik Ingress..."
kubectl apply -f "$PROJECT_DIR/k8s/ingress/traefik-deployment.yaml" >/dev/null

# Wait for Traefik to be ready
kubectl wait --for=condition=ready pod -l app=traefik -n traefik --timeout=60s 2>/dev/null || true

echo "✅ Infrastructure ready!"
echo ""
echo "Next step: ./scripts/app-deploy.sh"
