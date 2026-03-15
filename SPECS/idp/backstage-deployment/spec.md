# Feature: Backstage Deployment to Kubernetes

**Status**: Draft
**Tech Lead Review**: Not yet reviewed
**Branch**: sas-157-worker-deployments
**Working Directory**: `idp/`

## Summary
Deploy Backstage instance to Kubernetes (Minikube locally, cloud/on-prem production) with proper networking, persistence, and configuration for the Temporal OMS portal.

## Requirements

- Deploy Backstage to Minikube for local development
- Support Helm-based deployment for reproducibility
- Configure persistent storage for catalogs and metadata
- Set up database (PostgreSQL) for Backstage state
- Configure environment-specific settings (dev vs production)
- Enable Backstage plugins to authenticate with other systems
- Support multiple Backstage instances for different teams/organizations

## Acceptance Criteria

- [ ] Backstage pod running in Minikube with health checks passing
- [ ] PostgreSQL database accessible and initialized
- [ ] Backstage catalog loading without errors
- [ ] Can access Backstage UI via port-forward
- [ ] Configuration follows IaC patterns (Helm values, ConfigMaps)
- [ ] Startup and shutdown procedures documented

## Technical Approach

- Helm chart for Backstage deployment
- PostgreSQL for persistent storage (Docker/K8s in local, managed in production)
- ConfigMaps for configuration management
- Secrets for database credentials, API keys, etc.
- Standard K8s deployment patterns (Deployment, Service, PVC)
- Health checks and readiness probes

## Files Affected

- `k8s/backstage/` (new directory)
- `k8s/backstage/values.yaml` (Helm chart values)
- `k8s/backstage/deployment.yaml`
- `k8s/backstage/service.yaml`
- `k8s/postgres/` (if running locally)

## Risks & Constraints

- Database persistence: Must configure PVCs properly for local/cloud differences
- Memory requirements: Backstage can be memory-intensive
- PostgreSQL setup complexity: Must ensure proper initialization and backup

## Notes

Depends on: secrets-management (for database credentials, plugin API keys)
Related to: kubernetes-ingress-setup (for exposing Backstage UI)
