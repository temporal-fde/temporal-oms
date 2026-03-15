# Feature: Kubernetes Ingress Controller Setup

**Status**: Draft
**Tech Lead Review**: Not yet reviewed
**Branch**: sas-157-worker-deployments
**Working Directory**: `idp/`

## Summary
Install and configure Traefik ingress controller to expose Backstage portal and other services externally from Kubernetes cluster (Minikube, cloud, on-prem).

## Requirements

- Install Traefik ingress controller via Helm
- Configure DNS/routing for Backstage UI access
- Support HTTPS with self-signed certs (local dev) and valid certs (production)
- Route internal services through ingress (Backstage, Temporal UI, APIs)
- Support multiple domains/subdomains for different services
- Health checks and monitoring for ingress status

## Acceptance Criteria

- [ ] Traefik pod running in K8s cluster
- [ ] Can access Backstage UI via ingress URL (localhost:80 for Minikube)
- [ ] HTTPS configured with valid certificates
- [ ] Multiple services routed correctly through ingress
- [ ] Ingress rules follow Kubernetes best practices
- [ ] Documentation for adding new routes

## Technical Approach

- Traefik as ingress controller (light-weight, easy to configure)
- Helm chart for installation
- IngressRoute CRDs for routing rules
- Let's Encrypt integration for production HTTPS
- Self-signed certificates for local development

## Files Affected

- `idp/k8s/ingress/` (new directory)
- `idp/k8s/ingress/values.yaml` (Traefik Helm values)
- `idp/k8s/ingress/routes.yaml` (IngressRoute definitions)
- `idp/k8s/ingress/certificates.yaml` (TLS configuration)

## Risks & Constraints

- Port conflicts: Ingress uses ports 80/443 (may conflict in shared environments)
- Certificate management: Let's Encrypt renewal, self-signed cert replacement
- DNS resolution: Local dev requires /etc/hosts or local DNS

## Notes

Depends on: backstage-deployment (service to route to)
Related to: secrets-management (for TLS certificates)
