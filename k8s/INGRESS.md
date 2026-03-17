# Apps API Ingress Setup

The apps-api service is exposed via Traefik ingress controller, making it accessible from your local machine.

## Quick Start

```bash
# Full setup with ingress
./scripts/demo-up.sh

# In a new terminal, port-forward Traefik
./scripts/tunnel.sh

# Now you can access the API
curl http://localhost:8080/api/health
```

## Access Methods

### Method 1: Port-Forward (Recommended for local demo)

```bash
./scripts/tunnel.sh
# API available at: http://localhost:8080/api
```

This is the simplest method. Traefik will be port-forwarded to `localhost:8080`.

### Method 2: Using api.local Hostname

Add to your `/etc/hosts`:
```bash
echo "127.0.0.1 api.local" >> /etc/hosts
```

Then access via:
```bash
curl http://api.local/
# Note: requires port-forwarding or minikube tunnel
```

### Method 3: Direct Minikube IP (Advanced)

Get the Traefik external IP:
```bash
kubectl get svc -n traefik traefik
```

Access via the external IP:
```bash
curl http://<TRAEFIK_IP>/api
```

## API Endpoints

Apps API runs on port 8080 (HTTP) and 9090 (metrics). Via Traefik:

- **Main API**: `http://localhost:8080/api/*`
- **Health check**: `http://localhost:8080/api/actuator/health`
- **Metrics**: `http://localhost:8080/api/actuator/prometheus`
- **OpenAPI**: `http://localhost:8080/api/v3/api-docs`

## Routing Rules

Two ingress paths are configured:

1. **Host-based**: `api.local` → `/` (any path)
2. **Path-based**: `localhost` → `/api` prefix

So these all work:
```bash
curl http://localhost:8080/api/actuator/health
curl http://api.local/actuator/health  (with hosts entry)
```

## Testing the API

```bash
# Health check
curl http://localhost:8080/api/actuator/health

# List available endpoints
curl http://localhost:8080/api/actuator

# Get metrics
curl http://localhost:8080/api/actuator/prometheus

# OpenAPI spec
curl http://localhost:8080/api/v3/api-docs | jq
```

## Troubleshooting

**Cannot reach API:**
```bash
# Check tunnel is running
./scripts/tunnel.sh

# Check Traefik pods
kubectl get pods -n traefik

# Check Ingress is created
kubectl get ingress -n temporal-oms-apps
```

**Check Ingress status:**
```bash
kubectl describe ingress apps-api -n temporal-oms-apps
```

**View Traefik logs:**
```bash
kubectl logs -n traefik -l app.kubernetes.io/name=traefik -f
```

## Cleanup

Ingress is torn down with the rest of the demo:
```bash
./scripts/demo-down.sh
```

Or just remove Traefik:
```bash
./scripts/ingress-down.sh
```
