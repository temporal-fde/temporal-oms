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

# Install cert-manager (required by Temporal Worker Controller)
echo "→ Installing cert-manager..."
if ! kubectl get crd certificates.cert-manager.io &>/dev/null; then
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml >/dev/null
    until kubectl get deployment cert-manager -n cert-manager &>/dev/null; do sleep 2; done
    kubectl -n cert-manager wait --for=condition=available deployment/cert-manager --timeout=120s
    kubectl -n cert-manager wait --for=condition=available deployment/cert-manager-webhook --timeout=120s
    kubectl -n cert-manager wait --for=condition=available deployment/cert-manager-cainjector --timeout=120s
else
    echo "✓ cert-manager already installed"
fi

# Install Temporal Worker Controller CRDs
# CRDs live in a separate chart path as of v1.5.1: helm/temporal-worker-controller-crds/templates/
echo "→ Installing Temporal Worker Controller CRDs..."
if ! kubectl get crd temporalworkerdeployments.temporal.io &>/dev/null; then
    CRDS_BASE="https://raw.githubusercontent.com/temporalio/temporal-worker-controller/v1.5.1/helm/temporal-worker-controller-crds/templates"
    kubectl apply -f "${CRDS_BASE}/temporal.io_temporalconnections.yaml"
    kubectl apply -f "${CRDS_BASE}/temporal.io_temporalworkerdeployments.yaml"
    kubectl apply -f "${CRDS_BASE}/temporal.io_workerresourcetemplates.yaml"
    kubectl wait --for=condition=established crd/temporalworkerdeployments.temporal.io --timeout=60s
    kubectl wait --for=condition=established crd/temporalconnections.temporal.io --timeout=60s
    kubectl wait --for=condition=established crd/workerresourcetemplates.temporal.io --timeout=60s
else
    echo "✓ Temporal Worker Controller CRDs already installed"
fi

# Install Temporal Worker Controller
echo "→ Installing Temporal Worker Controller..."
if ! kubectl get deployment temporal-worker-controller-manager -n temporal-worker-controller-system &>/dev/null; then
    helm install temporal-worker-controller \
        oci://docker.io/temporalio/temporal-worker-controller \
        --namespace temporal-worker-controller-system \
        --create-namespace
else
    echo "✓ Temporal Worker Controller already installed"
fi

# Install Traefik Ingress Controller
echo "→ Installing Traefik Ingress..."
kubectl apply -f "$PROJECT_DIR/k8s/ingress/traefik-deployment.yaml" >/dev/null

# Wait for Traefik to be ready
kubectl wait --for=condition=ready pod -l app=traefik -n traefik --timeout=60s 2>/dev/null || true

# Apply cloud secrets from gitignored config files (never written to committed files)
if [ "${OVERLAY:-local}" = "cloud" ]; then
    echo "→ Applying cloud secrets from config/*.secret.yaml..."

    AUTOMATIONS_KEY=$(yq '.temporal.connection.api-key' "$PROJECT_DIR/config/acme.automations.secret.yaml")
    PROCESSING_KEY=$(yq '.temporal.connection.api-key' "$PROJECT_DIR/config/acme.processing.secret.yaml")
    APPS_KEY=$(yq '.temporal.connection.api-key' "$PROJECT_DIR/config/acme.apps.secret.yaml")

    # temporal-processing-api-key:
    #   TEMPORAL_API_KEY  → acme.automations key (used by Temporal Worker Controller's TemporalConnection)
    #   temporal-secret.yaml → acme.processing key (used by Spring app workers)
    kubectl create secret generic temporal-processing-api-key \
        -n temporal-oms-processing \
        --from-literal=TEMPORAL_API_KEY="$AUTOMATIONS_KEY" \
        --from-literal="temporal-secret.yaml=spring.temporal.connection.api-key: \"$PROCESSING_KEY\"" \
        --dry-run=client -o yaml | kubectl apply -f - >/dev/null

    # temporal-apps-api-key:
    #   temporal-secret.yaml → acme.apps key (used by Spring app workers)
    kubectl create secret generic temporal-apps-api-key \
        -n temporal-oms-apps \
        --from-literal="temporal-secret.yaml=spring.temporal.connection.api-key: \"$APPS_KEY\"" \
        --dry-run=client -o yaml | kubectl apply -f - >/dev/null
fi

echo "✅ Infrastructure ready!"
echo ""
echo "Next step: ./scripts/app-deploy.sh"
