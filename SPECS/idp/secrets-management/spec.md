# Feature: Secrets Management for Multi-Environment Deployments

**Status**: In Review
**Tech Lead Review**: Completed
**Branch**: main
**Working Directory**: `idp/`

## Summary
Portable secrets management system supporting local development, CI/CD, and production deployments across Kubernetes, Temporal Cloud, and cloud providers. Specifically handles Temporal Cloud API keys, mTLS certificates, and service credentials.

## Requirements

- Support local development (Minikube) without external dependencies
- Support CI/CD (GitHub Actions) with zero long-lived stored credentials
- Support production (Temporal Cloud, AWS/Azure/GCP) with audit logging
- Manage Temporal Cloud API keys and mTLS certificates
- Consistent secret access pattern across all environments
- Team members can add/rotate secrets without operations overhead

## Acceptance Criteria

- [ ] Local development can load secrets from .env without external services
- [ ] Sealed Secrets configured in Minikube with encryption at rest
- [ ] GitHub Actions workflows access secrets via OIDC tokens
- [ ] Doppler configured for production with External Secrets Operator
- [ ] Documentation covers all three environments
- [ ] Team can rotate Temporal Cloud API key without code changes

## Technical Approach

**Three-tier architecture:**
- **Local Dev**: Sealed Secrets + .env files
- **CI/CD**: GitHub Actions Secrets + OIDC tokens
- **Production**: Doppler + External Secrets Operator

See design document for detailed flows.

## Files Affected

- `k8s/secrets/` (new directory)
- `secrets/` (configuration templates)
- `../.github/workflows/` (updated with OIDC, relative to project root)
- `../DEPLOYMENT.md` (updated with secrets setup, relative to project root)
- `../.gitignore` (updated, relative to project root)

## Risks & Constraints

- Sealed Secrets: Limited to single K8s cluster (can't share across clusters)
- Doppler: Vendor SaaS dependency for production
- OIDC: Requires GitHub Actions token flow (CI/CD only)

## Notes

This is foundational - blocks all other specs that need to store/access credentials.
