# Demo Scripts

Modular scripts for managing the Temporal OMS demo environment.

## Quick Start

**First time setup (full demo):**
```bash
./scripts/demo-up.sh
```

**For live coding (after infrastructure is up):**
```bash
# Make code changes...
./scripts/app-deploy.sh
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
# Start Minikube, Temporal server, Traefik ingress, create namespaces
./scripts/infra-up.sh

# In another terminal, expose API via port-forward
./scripts/tunnel.sh

# ... make code changes ...

# Redeploy apps (fast - skips infra setup)
./scripts/app-deploy.sh

# Tear down just apps (keeps Minikube/Temporal/Traefik running)
./scripts/app-down.sh

# Stop everything
./scripts/infra-down.sh
```

### Check Status Anytime
```bash
./scripts/status.sh
```

## What Each Script Does

| Script | Purpose |
|--------|---------|
| `infra-up.sh` | Start Minikube, Temporal server, create namespaces, install Traefik ingress |
| `app-deploy.sh` | Build Java projects, build Docker images, deploy to Minikube |
| `app-down.sh` | Remove applications (keeps infrastructure running) |
| `infra-down.sh` | Stop Minikube, Temporal server, Traefik, remove everything |
| `demo-up.sh` | Full setup: runs infra-up + app-deploy |
| `demo-down.sh` | Full teardown: runs app-down + infra-down |
| `tunnel.sh` | Port-forward Traefik to localhost:8080 (run in another terminal) |
| `status.sh` | Show current deployment status |

## Live Coding Workflow

1. **Initial setup** (once per session):
   ```bash
   ./scripts/infra-up.sh
   ./scripts/app-deploy.sh
   ```

2. **Edit code** in your IDE

3. **Quick redeploy** (takes ~30 seconds):
   ```bash
   ./scripts/app-deploy.sh
   ```

4. **Repeat steps 2-3** as needed

5. **Clean up** when done:
   ```bash
   ./scripts/infra-down.sh
   ```

## Requirements

- `kubectl` - Kubernetes CLI
- `minikube` - Local Kubernetes cluster
- `docker` - Docker CLI (uses Minikube's Docker daemon)
- `temporal` - Temporal CLI for server (install: `brew install temporal`)
- Maven - For Java builds
- Java 21+ - For compiling

## Troubleshooting

**Pods stuck in ContainerCreating:**
```bash
./scripts/status.sh
kubectl describe pod POD_NAME -n NAMESPACE
```

**Need to see logs:**
```bash
kubectl logs -n temporal-oms-apps -l app=apps-worker -f
kubectl logs -n temporal-oms-processing -l app=processing-worker -f
```

**Reset everything:**
```bash
./scripts/demo-down.sh
./scripts/demo-up.sh
```
