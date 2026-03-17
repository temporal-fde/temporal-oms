# Secrets Management Guide

This guide explains how to use the file-based secrets management system in this project.

## Overview

The project uses **YAML-based secret files** that are mounted as files into Kubernetes pods at `/etc/config/secrets/`. This approach:
- ✅ Scales better than environment variables as secrets proliferate
- ✅ Works across all languages and frameworks
- ✅ Supports local dev, CI/CD, and production (via Doppler sync)
- ✅ Keeps secrets out of git with `.gitignore` patterns

## Local Development Setup

### 1. Create Secret Files from Templates

Copy the template files and fill in your actual values:

```bash
# Temporal Cloud credentials
cp config/temporal.secret.template.yaml config/temporal.secret.yaml

# IDP API credentials
cp config/idp.secret.yaml.template config/idp.secret.yaml

# Local environment overrides (optional)
cp config/environments/local.secret.yaml.template config/environments/local.secret.yaml
```

### 2. Edit Secret Files

Open each `.secret.yaml` file and replace `TODO` placeholders with actual values:

```bash
# Edit in your preferred editor
vim config/temporal.secret.yaml
vim config/idp.secret.yaml
```

### 3. Verify Files Exist

```bash
ls -la config/*.secret.yaml
ls -la config/environments/*.secret.yaml
```

**Important:** These files are `.gitignore`d and should **NEVER** be committed to git.

## Loading Secrets in Your Application

### By Language

#### Java
```java
import java.io.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

// Read secret file
String secretPath = System.getenv("CONFIG_PATH") + "/secrets/temporal.secret.yaml";
String content = Files.readString(Paths.get(secretPath));

// Parse YAML and load credentials
// (Use your YAML library: Jackson, SnakeYAML, etc.)
```

#### Python
```python
import os
import yaml

# Read secret file
config_path = os.getenv("CONFIG_PATH", "config")
with open(f"{config_path}/secrets/temporal.secret.yaml") as f:
    secrets = yaml.safe_load(f)

# Access credentials
api_key = secrets["temporal"]["cloudApiKey"]
```

#### TypeScript/Node.js
```typescript
import * as fs from "fs";
import * as yaml from "js-yaml";

// Read secret file
const configPath = process.env.CONFIG_PATH || "config";
const content = fs.readFileSync(`${configPath}/secrets/temporal.secret.yaml`, "utf-8");
const secrets = yaml.load(content);

// Access credentials
const apiKey = secrets.temporal.cloudApiKey;
```

#### Go
```go
package main

import (
    "io/ioutil"
    "os"
    "gopkg.in/yaml.v2"
)

// Read secret file
configPath := os.Getenv("CONFIG_PATH")
if configPath == "" {
    configPath = "config"
}

data, err := ioutil.ReadFile(configPath + "/secrets/temporal.secret.yaml")
if err != nil {
    // handle error
}

var secrets map[string]interface{}
yaml.Unmarshal(data, &secrets)
```

## Kubernetes Deployment

### 1. Prepare K8s Secret Manifests

When deploying to Kubernetes, you need to populate the K8s Secret manifests with your secret file contents.

#### Generate Base64-Encoded Content

```bash
# For Temporal secrets
base64 -i config/temporal.secret.yaml | pbcopy

# Then paste into k8s/secrets/temporal-secrets.yaml.template
# Replace the "TODO: Replace with base64-encoded..." placeholder
```

#### Apply Secret Manifests

```bash
# Apply the populated manifests (not .template versions)
kubectl apply -f k8s/secrets/temporal-secrets.yaml
kubectl apply -f k8s/secrets/idp-secrets.yaml
```

### 2. Verify Secrets Are Mounted

```bash
# Get pod name
POD=$(kubectl get pods -n temporal-oms -l app=apps-api -o jsonpath='{.items[0].metadata.name}')

# Verify secret files exist in pod
kubectl exec -it $POD -n temporal-oms -- ls -la /etc/config/secrets/

# Read a secret file to verify it's correct
kubectl exec -it $POD -n temporal-oms -- cat /etc/config/secrets/temporal/temporal.secret.yaml
```

### 3. Mount Paths in Pods

All containers mount secrets at:
- `/etc/config/secrets/temporal/temporal.secret.yaml` - Temporal credentials
- `/etc/config/secrets/idp/idp.secret.yaml` - IDP credentials

## Environment Variable Configuration

### Local Development

Set `CONFIG_PATH` to point to the local `config/` directory:

```bash
export CONFIG_PATH=config
```

Applications will then load secrets from `${CONFIG_PATH}/secrets/`.

### Kubernetes

When running in Kubernetes, containers automatically have access to mounted secrets at `/etc/config/secrets/`:

```yaml
volumeMounts:
- name: temporal-secrets
  mountPath: /etc/config/secrets/temporal
  readOnly: true
- name: idp-secrets
  mountPath: /etc/config/secrets/idp
  readOnly: true
```

Applications should use the default paths without needing to set `CONFIG_PATH`.

## Adding New Secret Types

To add a new component-scoped secret:

### 1. Create Template
```bash
cp config/TEMPLATE.secret.yaml.template config/mycomponent.secret.yaml.template
```

### 2. Add Documentation
Document what values are needed and where to obtain them in the template file.

### 3. Create K8s Manifest
```bash
cp k8s/secrets/TEMPLATE.secret.yaml.template k8s/secrets/mycomponent-secrets.yaml.template
```

### 4. Update Deployments
Add volume mounts in pod specs:
```yaml
volumeMounts:
- name: mycomponent-secrets
  mountPath: /etc/config/secrets/mycomponent
  readOnly: true
volumes:
- name: mycomponent-secrets
  secret:
    secretName: mycomponent-secrets
    defaultMode: 0400
```

## Troubleshooting

### Secret Files Not Found Locally

```bash
# Verify template files exist
ls -la config/*.secret.yaml.template

# Create from template
cp config/temporal.secret.template.yaml config/temporal.secret.yaml

# Check it was created
cat config/temporal.secret.yaml
```

### Secret Files Not Mounted in Pod

```bash
# Check if K8s Secret object exists
kubectl get secrets -n temporal-oms | grep temporal-secrets

# If missing, apply the manifest
kubectl apply -f k8s/secrets/temporal-secrets.yaml

# Verify mount in pod
kubectl exec -it <pod-name> -n temporal-oms -- ls -la /etc/config/secrets/
```

### Permission Denied Reading Secrets

Secrets are mounted with `defaultMode: 0400` (read-only for owner). If you get permission errors:

```bash
# Check pod user
kubectl exec -it <pod-name> -n temporal-oms -- whoami

# Check secret permissions
kubectl exec -it <pod-name> -n temporal-oms -- ls -la /etc/config/secrets/temporal/
```

### Applications Can't Find CONFIG_PATH

```bash
# Verify CONFIG_PATH is set (local dev)
echo $CONFIG_PATH

# Set if missing
export CONFIG_PATH=config

# Or add to your shell profile (.bashrc, .zshrc, etc.)
echo 'export CONFIG_PATH=config' >> ~/.zshrc
```

## CI/CD and Production

### CI/CD Pipeline

In CI/CD environments (GitHub Actions, GitLab CI, etc.):
1. Secrets are injected as files during build (not from `.secret.yaml` files)
2. Files are placed at expected mount paths before container starts
3. Deployment proceeds normally

### Production (Doppler Sync)

In production:
1. Doppler syncs secrets to a backend system
2. Operator mounts Doppler-managed secrets into K8s Secrets
3. Deployment proceeds normally

For details, see the infrastructure documentation.

## Best Practices

✅ **DO:**
- Keep `.secret.yaml` files local only (never commit)
- Use template files to document required secrets
- Set appropriate file permissions (`0400`)
- Rotate secrets regularly
- Use different secrets per environment

❌ **DON'T:**
- Commit actual `.secret.yaml` files to git
- Log or print secret contents
- Share secret files across environments
- Use the same secrets for dev/staging/prod
- Hardcode secrets in code

## References

- [Kubernetes Secrets Documentation](https://kubernetes.io/docs/concepts/configuration/secret/)
- [YAML Specification](https://yaml.org/)
- [Secret Management Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
