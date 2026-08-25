# Temporal Cloud Setup

Configure Temporal OMS Kubernetes deployments to connect to Temporal Cloud instead of a local
Temporal dev server.

> **First time?** Complete the one-time Temporal Cloud setup in [README.md](../README.md) Level 3,
> Step 1 before continuing here.

---

## Prerequisites

- Kubernetes deployment tools from [DEPLOYMENT.md](DEPLOYMENT.md): JDK 21, Maven, Docker, kubectl,
  Helm, yq, and either KinD or k3d. The matching `infra-up.sh` script creates the `temporal-oms`
  cluster if it does not already exist.
- Temporal Cloud namespaces and Nexus endpoints from [README.md](../README.md) Level 3.
- Four `config/*.secret.yaml` files populated with API keys:
  - `config/acme.apps.secret.yaml`
  - `config/acme.processing.secret.yaml`
  - `config/acme.fulfillment.secret.yaml`
  - `config/acme.automations.secret.yaml`
- Cloud ConfigMaps updated with your account's namespace and region values

---

## Deploy

```bash
# KinD
OVERLAY=cloud ./scripts/kind/infra-up.sh
OVERLAY=cloud ./scripts/kind/app-deploy.sh

# or k3d
OVERLAY=cloud ./scripts/k3d/infra-up.sh
OVERLAY=cloud ./scripts/k3d/app-deploy.sh
```

---

## Verification

```bash
# All pods healthy
./scripts/kind/status.sh
# or
./scripts/k3d/status.sh

# Worker Controller connected to Temporal Cloud
# Use /tmp/k3d-config.yaml for k3d.
export KUBECONFIG=/tmp/kind-config.yaml
kubectl get workerdeployment processing-workers -n temporal-oms-processing
# ConnectionHealthy: True

# App worker logs show connection to cloud
kubectl logs -n temporal-oms-processing -l app=processing-workers --tail=20
kubectl logs -n temporal-oms-apps -l app=apps-worker --tail=20

# Workflows are reachable
temporal workflow list \
  --address <your-region>.aws.api.temporal.io:7233 \
  --namespace apps.<your-account-id> \
  --api-key "$(yq '.temporal.connection.api-key' config/acme.apps.secret.yaml)" \
  --tls
```

---

## How Secrets Get Into the Cluster

`scripts/kind/infra-up.sh` and `scripts/k3d/infra-up.sh` read the gitignored
`config/*.secret.yaml` files when `OVERLAY=cloud` and create k8s secrets imperatively. No secret
values are ever written to committed files:

| config file | k8s secret | key | consumer |
|---|---|---|---|
| `config/acme.automations.secret.yaml` | `temporal-processing-api-key` | `TEMPORAL_API_KEY` | Temporal Worker Controller (`Connection`) |
| `config/acme.processing.secret.yaml` | `temporal-processing-api-key` | `temporal-secret.yaml` | Spring app workers (processing namespace) |
| `config/acme.apps.secret.yaml` | `temporal-apps-api-key` | `temporal-secret.yaml` | Spring app workers (apps namespace) |
| `config/acme.fulfillment.secret.yaml` | `temporal-fulfillment-api-key` | `temporal-secret.yaml` | Fulfillment workers |

---

## Troubleshooting

**`ConnectionHealthy: False`: `Request unauthorized`**
- The Worker Controller uses the `acme-automations-service-account` key, not the processing key
- Verify `config/acme.automations.secret.yaml` has the correct API key
- Re-run `OVERLAY=cloud ./scripts/kind/infra-up.sh` or `OVERLAY=cloud ./scripts/k3d/infra-up.sh`
  to re-apply the secret
- Verify `temporalNamespace` in the cloud overlay patch is `<namespace>.<account-id>` (fully qualified)

**`Request unauthorized` on all keys**
- Test with the CLI: `temporal workflow list --address <region>.aws.api.temporal.io:7233 --namespace <namespace>.<account-id> --api-key "..." --tls`
- The key may have been revoked. Regenerate it in Temporal Cloud > Settings > Identities.

**TLS handshake failures**
- Verify `TEMPORAL_TLS_ENABLED=true` is set in the cloud configmap overlay
- Verify `tls-server-name` matches your cloud hostname

**Pods in `CreateContainerConfigError`**
- Check pod events: `kubectl describe pod -n temporal-oms-processing -l app=processing-workers`
- Usually means a configmap or secret is missing. Re-run the matching `infra-up.sh` and `app-deploy.sh`.

**`processing-workers` pod not appearing**
- Check controller logs: `kubectl logs -n temporal-worker-controller-system deployment/temporal-worker-controller-manager -c manager --tail=30`
- Common causes: `Connection` unauthorized, bad namespace format, invalid rollout config

---

## Switching Back to Local

```bash
./scripts/kind/infra-down.sh
./scripts/kind/infra-up.sh
./scripts/kind/app-deploy.sh

# or
./scripts/k3d/infra-down.sh
./scripts/k3d/infra-up.sh
./scripts/k3d/app-deploy.sh
```
