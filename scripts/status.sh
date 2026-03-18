#!/bin/bash

export KUBECONFIG=/tmp/kind-config.yaml

echo "📊 Deployment Status"
echo ""
echo "Apps Namespace:"
kubectl get pods -n temporal-oms-apps --no-headers 2>/dev/null | awk '{printf "  %-40s %s\n", $1, $3}' || echo "  (namespace not found)"

echo ""
echo "Processing Namespace:"
kubectl get pods -n temporal-oms-processing --no-headers 2>/dev/null | awk '{printf "  %-40s %s\n", $1, $3}' || echo "  (namespace not found)"

echo ""
echo "Temporal Server:"
if pgrep -f "temporal server start-dev" >/dev/null 2>&1; then
    echo "  ✓ Running on localhost:7233"
else
    echo "  ✗ Not running"
fi

echo ""
echo "KinD Cluster:"
if kind get clusters 2>/dev/null | grep -q temporal-oms; then
    echo "  ✓ temporal-oms (running)"
else
    echo "  ✗ Not running"
fi
