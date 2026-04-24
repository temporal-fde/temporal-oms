#!/bin/bash

# Setup Temporal namespaces and Nexus endpoints for local development
# Creates 'apps', 'processing', and 'fulfillment' namespaces with cross-namespace Nexus endpoints

set -e

TEMPORAL_ADDRESS="${TEMPORAL_ADDRESS:-localhost:7233}"

echo "Setting up Temporal namespaces and Nexus endpoints..."
echo "Temporal Address: $TEMPORAL_ADDRESS"
echo ""

# Wait for Temporal server to be ready
echo "Waiting for Temporal server at $TEMPORAL_ADDRESS..."
until temporal operator namespace list --address "$TEMPORAL_ADDRESS" &>/dev/null; do
  echo "  server not ready, retrying in 2s..."
  sleep 2
done
echo "  server is ready"
echo ""

# Create apps namespace
echo "Creating namespace: apps"
temporal operator namespace create --address "$TEMPORAL_ADDRESS" --namespace apps 2>/dev/null || echo "  (apps namespace may already exist)"

# Create processing namespace
echo "Creating namespace: processing"
temporal operator namespace create --address "$TEMPORAL_ADDRESS" --namespace processing 2>/dev/null || echo "  (processing namespace may already exist)"

# Create fulfillment namespace
echo "Creating namespace: fulfillment"
temporal operator namespace create --address "$TEMPORAL_ADDRESS" --namespace fulfillment 2>/dev/null || echo "  (fulfillment namespace may already exist)"

echo ""
echo "Setting 'apps' Worker Deployment to build-id='local'"
echo ""
temporal worker deployment set-current-version \
  --address "$TEMPORAL_ADDRESS" \
  --deployment-name apps \
  --build-id local \
  --allow-no-pollers \
  --namespace apps \
  --yes 2>/dev/null || echo "  (skipped — start server with --dynamic-config-value system.enableDeploymentWorkflows=true)"

echo ""
echo "Setting 'processing' Worker Deployment to build-id='local'"
echo ""
temporal worker deployment set-current-version \
  --address "$TEMPORAL_ADDRESS" \
  --deployment-name processing \
  --build-id local \
  --allow-no-pollers \
  --namespace processing \
  --yes 2>/dev/null || echo "  (skipped — start server with --dynamic-config-value system.enableDeploymentWorkflows=true)"

echo ""
echo "Setting 'fulfillment' Worker Deployment to as build-id='local'"
echo ""
temporal worker deployment set-current-version \
  --address "$TEMPORAL_ADDRESS" \
  --deployment-name fulfillment \
  --build-id local \
  --allow-no-pollers \
  --namespace fulfillment \
  --yes 2>/dev/null || echo "  (skipped — start server with --dynamic-config-value system.enableDeploymentWorkflows=true)"

echo ""
echo "Registering Nexus endpoints..."
echo ""

echo "Registering endpoint 'oms-processing-v1' in apps namespace"
temporal operator nexus endpoint create \
  --address "$TEMPORAL_ADDRESS" \
  --name "oms-processing-v1" \
  --target-namespace processing \
  --target-task-queue processing 2>/dev/null || echo "  (endpoint may already exist)"

echo "Registering endpoint 'oms-apps-v1' in processing namespace"
temporal operator nexus endpoint create \
  --address "$TEMPORAL_ADDRESS" \
  --name "oms-apps-v1" \
  --target-namespace apps \
  --target-task-queue apps 2>/dev/null || echo "  (endpoint may already exist)"

echo "Registering endpoint 'oms-integrations-v1' targeting apps/integrations task queue"
temporal operator nexus endpoint create \
  --address "$TEMPORAL_ADDRESS" \
  --name "oms-integrations-v1" \
  --target-namespace apps \
  --target-task-queue integrations 2>/dev/null || echo "  (endpoint may already exist)"

echo "Registering endpoint 'oms-fulfillment-v1' targeting fulfillment task queue"
temporal operator nexus endpoint create \
  --address "$TEMPORAL_ADDRESS" \
  --name "oms-fulfillment-v1" \
  --target-namespace fulfillment \
  --target-task-queue fulfillment 2>/dev/null || echo "  (endpoint may already exist)"

echo ""
echo "Registering custom search attributes..."
echo ""

# margin_leak: records shipping cost overage (cents) on fulfillment.Order workflows
temporal operator search-attribute create \
  --address "$TEMPORAL_ADDRESS" \
  --namespace fulfillment \
  --name margin_leak \
  --type Int 2>/dev/null || echo "  (margin_leak attribute may already exist)"

echo ""
echo "✓ Setup complete!"
echo ""
echo "To run workers with these namespaces:"
echo "  export TEMPORAL_NAMESPACE=apps        # Java apps worker"
echo "  export TEMPORAL_NAMESPACE=processing   # Java processing worker"
echo "  export TEMPORAL_NAMESPACE=fulfillment # Python fulfillment worker"
echo "  export TEMPORAL_ADDRESS=localhost:7233"