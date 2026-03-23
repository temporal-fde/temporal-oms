# Temporal Cloud Setup

Configure Temporal OMS to connect to Temporal Cloud instead of a local Temporal server.

> **First time?** Complete the one-time Temporal Cloud setup in [README.md](README.md) — Level 3, Step 1 before continuing here.

---

## Prerequisites

- KinD cluster running (`kind get clusters` shows `temporal-oms`)
- Three `config/*.secret.yaml` files populated with API keys:
  - `config/acme.apps.secret.yaml`
  - `config/acme.processing.secret.yaml`
  - `config/acme.automations.secret.yaml`
- Cloud ConfigMaps updated with your account's namespace and region values

---

## Deploy

```bash
OVERLAY=cloud ./scripts/infra-up.sh    # installs controller, applies secrets from config/*.secret.yaml
OVERLAY=cloud ./scripts/app-deploy.sh  # builds images, deploys all apps
```

---

## Verification

```bash
# All pods healthy
./scripts/status.sh

# Worker Controller connected to Temporal Cloud
export KUBECONFIG=/tmp/kind-config.yaml
kubectl get temporalworkerdeployment processing-workers -n temporal-oms-processing
# TemporalConnectionHealthy: True

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

`infra-up.sh` (when `OVERLAY=cloud`) reads the gitignored `config/*.secret.yaml` files and
creates k8s secrets imperatively — no secret values are ever written to committed files:

| config file | k8s secret | key | consumer |
|---|---|---|---|
| `config/acme.automations.secret.yaml` | `temporal-processing-api-key` | `TEMPORAL_API_KEY` | Temporal Worker Controller (`TemporalConnection`) |
| `config/acme.processing.secret.yaml` | `temporal-processing-api-key` | `temporal-secret.yaml` | Spring app workers (processing namespace) |
| `config/acme.apps.secret.yaml` | `temporal-apps-api-key` | `temporal-secret.yaml` | Spring app workers (apps namespace) |

---

## Troubleshooting

**`TemporalConnectionHealthy: False` — `Request unauthorized`**
- The Worker Controller uses the `acme-automations-service-account` key, not the processing key
- Verify `config/acme.automations.secret.yaml` has the correct API key
- Re-run `OVERLAY=cloud ./scripts/infra-up.sh` to re-apply the secret
- Verify `temporalNamespace` in the cloud overlay patch is `<namespace>.<account-id>` (fully qualified)

**`Request unauthorized` on all keys**
- Test with the CLI: `temporal workflow list --address <region>.aws.api.temporal.io:7233 --namespace <namespace>.<account-id> --api-key "..." --tls`
- The key may have been revoked — regenerate in Temporal Cloud → Settings → Identities

**TLS handshake failures**
- Verify `TEMPORAL_TLS_ENABLED=true` is set in the cloud configmap overlay
- Verify `tls-server-name` matches your cloud hostname

**Pods in `CreateContainerConfigError`**
- Check pod events: `kubectl describe pod -n temporal-oms-processing -l app=processing-workers`
- Usually means a configmap or secret is missing — re-run `infra-up.sh` and `app-deploy.sh`

**`processing-workers` pod not appearing**
- Check controller logs: `kubectl logs -n temporal-worker-controller-system deployment/temporal-worker-controller-manager -c manager --tail=30`
- Common causes: `TemporalConnection` unauthorized, bad namespace format, invalid rollout config

---

## Switching Back to Local

```bash
./scripts/infra-down.sh   # destroy cluster
./scripts/infra-up.sh     # rebuild with OVERLAY=local (default)
./scripts/app-deploy.sh
```
