#!/bin/bash

echo "🔌 Tearing down infrastructure..."

export KUBECONFIG=/tmp/kind-config.yaml

# Stop apps first
echo "→ Stopping applications..."
kubectl delete namespace temporal-oms-apps temporal-oms-processing 2>/dev/null || true

# Stop Traefik
echo "→ Stopping Traefik..."
kubectl delete namespace traefik 2>/dev/null || true

# Delete KinD cluster
echo "→ Deleting KinD cluster..."
kind delete cluster --name temporal-oms 2>/dev/null || true

echo "✅ Infrastructure stopped"
