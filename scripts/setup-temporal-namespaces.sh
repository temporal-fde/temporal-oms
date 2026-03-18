#!/bin/bash

# Setup Temporal namespaces and Nexus endpoints for local development
# Creates 'apps' and 'processing' namespaces with cross-namespace Nexus endpoints

set -e

TEMPORAL_ADDRESS="${TEMPORAL_ADDRESS:-localhost:7233}"

echo "Setting up Temporal namespaces and Nexus endpoints..."
echo "Temporal Address: $TEMPORAL_ADDRESS"
echo ""

# Create apps namespace
echo "Creating namespace: apps"
#temporal namespace create \
#  --address "$TEMPORAL_ADDRESS" \
#  --namespace "apps" \
#  2>/dev/null || echo "  (apps namespace may already exist)"

temporal operator namespace create --namespace apps

# Create processing namespace
echo "Creating namespace: processing"
#temporal namespace create \
#  --address "$TEMPORAL_ADDRESS" \
#  --namespace "processing" \
#  2>/dev/null || echo "  (processing namespace may already exist)"

temporal operator namespace create --namespace processing

echo ""
echo "Registering Nexus endpoints..."
echo ""

# Apps namespace: order-processing endpoint -> oms-processing-v1 service
echo "Registering endpoint 'oms-processing-v1' in apps namespace"
#temporal nexus endpoint create \
#  --address "$TEMPORAL_ADDRESS" \
#  --namespace "apps" \
#  --name "order-processing" \
#  --target-service "oms-processing-v1" \
#  2>/dev/null || echo "  (endpoint may already exist)"
temporal operator nexus endpoint create \
  --name "oms-processing-v1" \
  --target-namespace processing \
  --target-task-queue processing

# Processing namespace: apps endpoint -> oms-apps-v1 service
echo "Registering endpoint 'apps' in processing namespace"
#temporal nexus endpoint create \
#  --address "$TEMPORAL_ADDRESS" \
#  --namespace "apps" \
#  --name "acme-apps-v1" \
#  --target-service "oms-apps-v1" \
#  2>/dev/null || echo "  (endpoint may already exist)"

temporal operator nexus endpoint create \
  --name "oms-apps-v1" \
  --target-namespace apps \
  --target-task-queue apps

echo ""
echo "✓ Setup complete!"
echo ""
echo "To run workers with these namespaces:"
echo "  export TEMPORAL_NAMESPACE=apps"
echo "  export TEMPORAL_ADDRESS=localhost:7233"