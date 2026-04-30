# Demo Scripts

Modular scripts for managing the Temporal OMS Kubernetes deployment with either KinD or k3d.

> For complete deployment documentation including Temporal Cloud API key setup, see [../DEPLOYMENT.md](../DEPLOYMENT.md).

## Runtime Paths

| Path | Purpose |
|---|---|
| `scripts/kind/*` | KinD implementation |
| `scripts/k3d/*` | k3d implementation |

The two cluster-specific directories intentionally duplicate the small driver scripts. This keeps
the operational paths easy to read and avoids cluster-driver conditionals inside every shell script.

## Quick Start

KinD with Temporal Cloud:

```bash
OVERLAY=cloud ./scripts/kind/demo-up.sh
```

k3d with Temporal Cloud:

```bash
OVERLAY=cloud ./scripts/k3d/demo-up.sh
```

KinD with local Temporal:

```bash
temporal server start-dev
OVERLAY=local ./scripts/kind/demo-up.sh
```

k3d with local Temporal:

```bash
temporal server start-dev --ip 0.0.0.0 --ui-ip 0.0.0.0
OVERLAY=local ./scripts/k3d/demo-up.sh
```

For live coding after infrastructure is up:

```bash
OVERLAY=cloud ./scripts/kind/app-deploy.sh
OVERLAY=local ./scripts/k3d/app-deploy.sh
```

Tear everything down:

```bash
./scripts/kind/demo-down.sh
./scripts/k3d/demo-down.sh
```

## Modular Workflow

Use one directory consistently for a session:

```bash
./scripts/kind/infra-up.sh
./scripts/kind/tunnel.sh
OVERLAY=cloud ./scripts/kind/app-deploy.sh
./scripts/kind/app-down.sh
./scripts/kind/infra-down.sh
```

```bash
./scripts/k3d/infra-up.sh
./scripts/k3d/tunnel.sh
OVERLAY=local ./scripts/k3d/app-deploy.sh
./scripts/k3d/app-down.sh
./scripts/k3d/infra-down.sh
```

Check status anytime:

```bash
./scripts/kind/status.sh
./scripts/k3d/status.sh
```

Run demo scenarios:

```bash
./scripts/runscenario.sh
./scripts/runscenario.sh valid-order --yes
```

## What Each Cluster Directory Provides

| Script | Purpose |
|---|---|
| `infra-up.sh` | Create cluster, create namespaces, install cert-manager, TWC, and Traefik |
| `app-deploy.sh` | Build Java projects, build Docker images, load/import images, deploy apps |
| `app-down.sh` | Remove applications while keeping the cluster running |
| `infra-down.sh` | Delete the cluster and all infrastructure |
| `demo-up.sh` | Full setup: runs `infra-up.sh` and `app-deploy.sh` |
| `demo-down.sh` | Full teardown: runs `app-down.sh` and `infra-down.sh` |
| `deploy-processing-workers.sh` | Build and deploy a new processing worker image through TWC |
| `tunnel.sh` | Port-forward APIs |
| `status.sh` | Show deployment status |

## Requirements

- `kubectl`
- `docker`
- `kind` for `scripts/kind/*`
- `k3d` for `scripts/k3d/*`
- `helm`
- `temporal`
- Maven and Java 21+

## Overlays

Scripts support environment overlays through `OVERLAY`:

```bash
OVERLAY=cloud ./scripts/kind/demo-up.sh
OVERLAY=local ./scripts/kind/demo-up.sh
OVERLAY=local ./scripts/k3d/demo-up.sh
```

Default is `local` if `OVERLAY` is not set.

## Troubleshooting

Pods stuck in `ContainerCreating`:

```bash
./scripts/kind/status.sh
./scripts/k3d/status.sh
kubectl describe pod POD_NAME -n NAMESPACE
```

Need logs:

```bash
kubectl logs -n temporal-oms-apps -l app=apps-worker -f
kubectl logs -n temporal-oms-processing -l app=processing-workers -f
```

Reset everything:

```bash
./scripts/kind/demo-down.sh
./scripts/kind/demo-up.sh

./scripts/k3d/demo-down.sh
./scripts/k3d/demo-up.sh
```
