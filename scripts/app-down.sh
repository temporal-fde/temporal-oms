#!/bin/bash
set -e

export KUBECONFIG=/tmp/kind-config.yaml

echo "🗑️  Removing applications..."

kubectl delete namespace \
  temporal-oms-apps \
  temporal-oms-processing \
  temporal-oms-fulfillment \
  temporal-oms-enablements \
  2>/dev/null || true

echo "✅ Applications removed"
