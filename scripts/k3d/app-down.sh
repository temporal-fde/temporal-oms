#!/bin/bash
set -e

export KUBECONFIG=/tmp/k3d-config.yaml

echo "🗑️  Removing k3d applications..."

kubectl delete namespace \
  temporal-oms-apps \
  temporal-oms-processing \
  temporal-oms-fulfillment \
  temporal-oms-enablements \
  2>/dev/null || true

echo "✅ k3d applications removed"
