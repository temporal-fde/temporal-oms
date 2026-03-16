# Feature: Secrets Management for Multi-Environment Deployments

**Status**: In Review
**Tech Lead Review**: Completed
**Branch**: sas-157-worker-deployments
**Working Directory**: `idp/`

## Summary
Portable, component-scoped secrets management system supporting local development, CI/CD, and production deployments across Kubernetes, Temporal Cloud, and cloud providers. Secrets are mounted as files into pods, allowing each application/language to load them as needed. Specifically handles Temporal Cloud API keys, mTLS certificates, and service credentials.

## Requirements

- Support local development (Minikube) without external dependencies
- Support CI/CD (GitHub Actions) with zero long-lived stored credentials
- Support production (Temporal Cloud, AWS/Azure/GCP) with audit logging
- Manage component-scoped secrets: Temporal Cloud, IDP API, databases, external services
- File-based secrets mounted in pods (each language loads as needed)
- Consistent secret naming and file structure across all environments
- Team members can add/rotate secrets without code changes
- Secrets organized by component (temporal.secret.yaml, idp.secret.yaml, etc.)

## Acceptance Criteria

- [ ] Local development can load secrets from `{component}.secret.yaml` files
- [ ] `.secret.yaml.template` files document required secrets for each component
- [ ] K8s ConfigMaps/Secrets mounted at `/etc/config/` in pods
- [ ] GitHub Actions injects secrets into test pods
- [ ] Doppler configured for production with External Secrets Operator syncing to Secret objects
- [ ] Secrets mounted as files to `/etc/config/secrets/{component}.secret.yaml`
- [ ] `.gitignore` prevents committing `*.secret.yaml` files
- [ ] Documentation covers all three environments and loading mechanisms
- [ ] Multiple languages (Java, Python, Go, TypeScript) can load secrets

## Technical Approach

**File-mount architecture:**
- Each component has secrets in `{component}.secret.yaml`
- Secrets mounted as K8s Secret/ConfigMap volumes to `/etc/config/`
- Applications read `/etc/config/{component}.secret.yaml` at startup
- Language-agnostic: each stack loads YAML/JSON as it prefers

**Three-tier implementation:**
1. **Local Dev**: Files on filesystem
   - `config/{component}.secret.yaml` (git-ignored)
   - `config/{component}.secret.yaml.template` (git-tracked, documents required fields)
   - Apps read from local paths

2. **CI/CD**: Files injected via K8s mounts
   - GitHub Actions creates Secret manifests from secrets
   - Secrets mounted into test/build pods
   - Apps read from pod mount paths

3. **Production**: Doppler synced to K8s Secrets
   - Doppler stores all secrets (one per environment)
   - External Secrets Operator watches Doppler
   - Creates K8s Secret objects
   - Secrets mounted into production pods
   - Apps read from pod mount paths

## Files Affected

- `config/` (project root - config directory exists)
- `config/{component}.secret.yaml` (git-ignored - actual secrets)
- `config/{component}.secret.yaml.template` (git-tracked - template for developers)
- `config/environments/{env}.secret.yaml` (git-ignored - environment overrides)
- `config/environments/{env}.secret.yaml.template` (git-tracked)
- `k8s/configmaps/` (ConfigMap manifests for non-secret config)
- `k8s/secrets/` (Secret manifests for mounted secrets)
- `k8s/external-secrets/` (External Secrets Operator configuration)
- `../.gitignore` (updated to ignore `*.secret.yaml`, relative to project root)
- `../DEPLOYMENT.md` (updated with secrets setup, relative to project root)

## Example Structure

```
config/
├── temporal.yaml (non-secret config)
├── temporal.secret.yaml.template (git-tracked)
├── temporal.secret.yaml (git-ignored - created from template locally)
├── idp.yaml
├── idp.secret.yaml.template
├── idp.secret.yaml (git-ignored)
└── environments/
    ├── local.yaml
    ├── local.secret.yaml.template
    ├── local.secret.yaml (git-ignored)
    ├── dev.secret.yaml.template
    ├── prod.secret.yaml.template
    └── (actual secret files managed by Doppler in CI/CD & prod)

k8s/
├── configmaps/
│   ├── temporal-configmap.yaml
│   └── idp-configmap.yaml
├── secrets/
│   ├── temporal-secrets.yaml
│   └── idp-secrets.yaml
└── external-secrets/
    └── doppler-externalsecretsoperator.yaml
```

## Pod Mount Example

```yaml
# K8s Deployment
spec:
  containers:
  - name: api
    volumeMounts:
    - name: config
      mountPath: /etc/config
      readOnly: true
    - name: secrets
      mountPath: /etc/config/secrets
      readOnly: true
  volumes:
  - name: config
    configMap:
      name: temporal-configmap
  - name: secrets
    secret:
      secretName: temporal-secrets
      defaultMode: 0400  # read-only for owner
```

## Risks & Constraints

- File permissions: Must ensure secret files have restrictive permissions (0400)
- Pod debugging: Developers can `kubectl exec` and read mounted secrets (normal risk)
- Doppler: Vendor SaaS dependency for production (can be replaced with Vault)
- Template maintenance: Templates must stay in sync as secrets evolve
- Local dev setup: Developers must create `.secret.yaml` from templates

## Notes

This is foundational - blocks all other specs that need to store/access credentials.

### Component Examples

**temporal.secret.yaml.template**:
```yaml
# Temporal Cloud credentials
temporal:
  cloudApiKey: "TODO: Get from Temporal Cloud account"
  namespace: "TODO: e.g., my-project-dev.tmprl.cloud"
  clientCertPath: "/etc/config/secrets/temporal-client.pem"
  clientKeyPath: "/etc/config/secrets/temporal-client.key"
```

**idp.secret.yaml.template**:
```yaml
# IDP API credentials
idp:
  apiKey: "TODO: Generate internal API key"
  backendSecret: "TODO: Backend-to-backend auth secret"
  databasePassword: "TODO: PostgreSQL password"
```

### Loading Pattern (Language-agnostic)
- Java: `ObjectMapper().readValue(new File("/etc/config/temporal.secret.yaml")...)`
- Python: `yaml.safe_load(open('/etc/config/temporal.secret.yaml'))`
- Go: `yaml.Unmarshal(data, &config)`
- TypeScript: `YAML.parse(fs.readFileSync('/etc/config/temporal.secret.yaml'))`
