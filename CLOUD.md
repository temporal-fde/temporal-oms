# Temporal Cloud Setup

Configure the Temporal OMS applications to connect to Temporal Cloud instead of a local Temporal server.

## Quick Start

For complete step-by-step instructions, see [DEPLOYMENT.md](DEPLOYMENT.md) — **Section: Temporal Cloud API Key Setup**.

## Overview

Temporal Cloud deployment requires:

1. **Temporal Cloud Account**: Create at https://cloud.temporal.io
2. **API Key**: Generated in Temporal Cloud console (JWT format)
3. **Namespace**: Your Temporal Cloud namespace (e.g., `fde-oms-apps.account-id`)
4. **Region**: Your Temporal Cloud region endpoint (e.g., `us-east-1.aws.api.temporal.io:7233`)

## Configuration Steps

### Step 1: Get API Key from Temporal Cloud Console

1. Log in to [https://cloud.temporal.io](https://cloud.temporal.io)
2. Navigate to **Settings → API Keys**
3. Create or copy your API key (JWT format)
4. Note your:
   - Namespace ID
   - Account ID
   - Region endpoint

### Step 2: Verify with Temporal CLI

Configure your local Temporal CLI to verify connectivity:

```bash
# Set up environment
temporal env set --env fde-oms-apps \
  --address us-east-1.aws.api.temporal.io:7233 \
  --api-key "eyJhbGc..." \
  --namespace fde-oms-apps.account-id

# Test connection
temporal workflow list --env fde-oms-apps
```

This should list your workflows (even if empty).

### Step 3: Configure Kubernetes Secrets

Store your API keys in Kubernetes Secrets for deployment:

#### For Apps Workers:

Update or create `k8s/overlays/cloud/secrets/temporal-apps-api-key.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: temporal-apps-api-key
  namespace: temporal-oms-apps
type: Opaque
stringData:
  temporal-secret.yaml: |
    spring.temporal.connection.api-key: "eyJhbGc..."
```

#### For Processing Workers:

Update or create `k8s/overlays/cloud/secrets/temporal-processing-api-key.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: temporal-processing-api-key
  namespace: temporal-oms-processing
type: Opaque
stringData:
  temporal-secret.yaml: |
    spring.temporal.connection.api-key: "eyJhbGc..."
```

**Important**: These files contain secrets and should NOT be committed to git. They're already in `.gitignore`.

### Step 4: Update ConfigMap for Your Cloud Region

Update `k8s/overlays/cloud/configmap/temporal-apps.yaml`:

```yaml
spring:
  temporal:
    namespace: fde-oms-apps.account-id
    connection:
      target: us-east-1.aws.api.temporal.io:7233  # Your region
      tls-server-name: us-east-1.aws.api.temporal.io
      tls:
        enabled: true
```

(Replace with your actual namespace, account ID, and region endpoint)

### Step 5: Deploy to KinD

```bash
export KUBECONFIG=/tmp/kind-config.yaml
OVERLAY=cloud ./scripts/demo-up.sh
```

## Verification

After deployment, verify connectivity:

```bash
# Check pods are running
./scripts/status.sh

# View logs to see connection messages
export KUBECONFIG=/tmp/kind-config.yaml
kubectl logs -n temporal-oms-apps -l app=apps-worker --tail=20
kubectl logs -n temporal-oms-processing -l app=processing-worker --tail=20

# Verify workflows are executing
temporal workflow list --env fde-oms-apps
```

## Troubleshooting

**TLS handshake failures:**
- Verify `tls.enabled: true` is set
- Verify `tls-server-name` matches your cloud hostname
- Check API key format (should be JWT token starting with `eyJ...`)

**Connection refused:**
- Verify API key is correct and hasn't expired
- Verify namespace matches your Temporal Cloud setup
- Verify region endpoint is correct

**For more details:**
See [DEPLOYMENT.md](DEPLOYMENT.md) — **Troubleshooting** section

## Local Fallback

To use a local Temporal server instead:

```bash
# Start local Temporal
temporal server start-dev &

# Deploy with local overlay
OVERLAY=local ./scripts/demo-up.sh
```

See [DEPLOYMENT.md](DEPLOYMENT.md) — **Option 2: Local Temporal Setup**

## Resources

- [Temporal Cloud Console](https://cloud.temporal.io/)
- [Temporal Cloud API Keys Documentation](https://docs.temporal.io/cloud/api-keys)
- [Temporal Cloud Namespaces](https://docs.temporal.io/cloud/namespaces)
