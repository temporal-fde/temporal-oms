# Demo Scripts

Modular scripts for managing the Temporal OMS Kubernetes deployment with KinD.

> For complete deployment documentation including Temporal Cloud API key setup, see [../DEPLOYMENT.md](../DEPLOYMENT.md)

## Quick Start

**For Temporal Cloud deployment (OVERLAY=cloud):**
```bash
OVERLAY=cloud ./scripts/demo-up.sh
```

**For local Temporal deployment (OVERLAY=local):**
```bash
OVERLAY=local ./scripts/demo-up.sh
```

**For live coding (after infrastructure is up):**
```bash
# Make code changes...
OVERLAY=cloud ./scripts/app-deploy.sh
# Repeat as needed
```

**Tear everything down:**
```bash
./scripts/demo-down.sh
```

## Modular Workflow

For more control, use individual scripts:

### Infrastructure Only
```bash
# Create KinD cluster, create namespaces, install Traefik ingress
./scripts/infra-up.sh

# In another terminal, expose API via port-forward
./scripts/tunnel.sh

# ... make code changes ...

# Redeploy apps (fast - skips infra setup)
OVERLAY=cloud ./scripts/app-deploy.sh

# Tear down just apps (keeps KinD cluster running)
./scripts/app-down.sh

# Stop everything (delete KinD cluster)
./scripts/infra-down.sh
```

### Check Status Anytime
```bash
./scripts/status.sh
```

## What Each Script Does

| Script | Purpose |
|--------|---------|
| `infra-up.sh` | Create KinD cluster, create namespaces, install Traefik ingress |
| `app-deploy.sh` | Build Java projects, build Docker images, load to KinD, deploy apps |
| `app-down.sh` | Remove applications (keeps KinD cluster running) |
| `infra-down.sh` | Delete KinD cluster and all infrastructure |
| `demo-up.sh` | Full setup: runs infra-up + app-deploy |
| `demo-down.sh` | Full teardown: runs app-down + infra-down |
| `tunnel.sh` | Port-forward Traefik to localhost:8080 (run in another terminal) |
| `status.sh` | Show current deployment status (pods, KinD cluster, Temporal server)

## Live Coding Workflow

1. **Initial setup** (once per session):
   ```bash
   OVERLAY=cloud ./scripts/demo-up.sh
   ```

2. **Port-forward** (in another terminal):
   ```bash
   ./scripts/tunnel.sh
   ```

3. **Edit code** in your IDE

4. **Quick redeploy** (takes ~30 seconds):
   ```bash
   OVERLAY=cloud ./scripts/app-deploy.sh
   ```

5. **Repeat steps 3-4** as needed

6. **Clean up** when done:
   ```bash
   ./scripts/demo-down.sh
   ```

## Requirements

- `kubectl` - Kubernetes CLI
- `kind` - KinD (Kubernetes in Docker) cluster
- `docker` - Docker CLI
- `temporal` - Temporal CLI for server (install: `brew install temporal`)
- Maven - For Java builds (uses asdf from .tool-versions)
- Java 21+ - For compiling (uses asdf from .tool-versions)

## Overlays

Scripts support environment overlays via `OVERLAY` variable:

```bash
# Temporal Cloud deployment (requires API key setup - see DEPLOYMENT.md)
OVERLAY=cloud ./scripts/demo-up.sh

# Local Temporal deployment (uses host.docker.internal:7233)
OVERLAY=local ./scripts/demo-up.sh

# Default is 'local' if not specified
./scripts/demo-up.sh
```

## Troubleshooting

**Pods stuck in ContainerCreating:**
```bash
./scripts/status.sh
kubectl describe pod POD_NAME -n NAMESPACE
```

**Need to see logs:**
```bash
kubectl logs -n temporal-oms-apps -l app=apps-worker -f
kubectl logs -n temporal-oms-processing -l app=processing-workers -f
```

**Reset everything:**
```bash
./scripts/demo-down.sh
./scripts/demo-up.sh
```
