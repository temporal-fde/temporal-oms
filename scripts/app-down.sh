#!/bin/bash
set -e

echo "🗑️  Removing applications..."

kubectl delete namespace temporal-oms-apps temporal-oms-processing 2>/dev/null || true

echo "✅ Applications removed"
