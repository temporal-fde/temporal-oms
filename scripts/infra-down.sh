#!/bin/bash

echo "🔌 Tearing down infrastructure..."

# Stop apps first
echo "→ Stopping applications..."
kubectl delete namespace temporal-oms-apps temporal-oms-processing 2>/dev/null || true

# Stop Traefik
echo "→ Stopping Traefik..."
helm uninstall traefik -n traefik --ignore-not-found 2>/dev/null || true

# Stop Temporal server
echo "→ Stopping Temporal server..."
pkill -f "temporal server start-dev" || true

# Stop Minikube
echo "→ Stopping Minikube..."
minikube stop

echo "✅ Infrastructure stopped"
