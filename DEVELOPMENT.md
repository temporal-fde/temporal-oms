# Development Guide

Reference for day-to-day development on the Temporal OMS project — modifying workflows, regenerating protobufs, running tests, and debugging.

For getting the system running locally for the first time, see [GETTING_STARTED.md](GETTING_STARTED.md).

---

## Modifying Protocol Buffers

When you change `.proto` files:

```bash
cd proto

# Check for errors
buf lint

# Check for breaking changes
buf breaking --against '.git#branch=main'

# Regenerate code for all languages
buf generate
```

This regenerates:
- `java/generated/` — Java classes
- `python/generated/` — Python stubs
- `web/src/lib/generated/` — TypeScript

Then rebuild Java services:
```bash
cd java
mvn clean install
```

---

## Making Changes to Workflows

1. Edit the workflow implementation (e.g. `java/apps/apps-core/src/main/java/.../OrderImpl.java`)
2. Rebuild: `mvn clean package`
3. Restart the worker terminal (Ctrl+C, then re-run)
4. New workflow instances use the updated code; in-flight instances continue on the old code

> **Worker Versioning note:** When running locally without the Temporal Worker Controller, restarting a worker does not change the current version — it just restarts the same build-id. If you need a new version to be the current version (e.g. to test versioning behavior), re-run `scripts/setup-temporal-namespaces.sh` with a different `--build-id`. In Kubernetes, bumping the image tag is the version trigger — see [java/enablements/README.md](java/enablements/README.md).

---

## Adding New Activities

1. Define the interface in `*-core/src/main/java/...Activities.java`
2. Implement it in `*-core/src/main/java/.../ActivitiesImpl.java`
3. Register the bean in worker configuration
4. Call it from the workflow

---

## Testing

```bash
cd java

# Run all tests
mvn test

# Run a specific test class
mvn test -Dtest=OrderImplTest

# Run with Temporal debug logging
mvn test -Dlogging.level.io.temporal=DEBUG
```

---

## Debugging

### Enable Debug Logging

Add or update logging config in the relevant `application.yaml`:

```yaml
logging:
  level:
    root: INFO
    com.acme: DEBUG
    io.temporal: DEBUG
```

Restart the service for it to take effect.

### View Workflow History

```bash
# Via Temporal UI
open http://localhost:8233/namespaces/apps/workflows/{orderId}

# Via CLI — show all events
temporal workflow show --workflow-id {orderId} --namespace apps

# Via CLI — describe current state
temporal workflow describe --workflow-id {orderId} --namespace apps

# Via CLI — query workflow state
temporal workflow query \
  --workflow-id {orderId} \
  --namespace apps \
  --type getState
```

### Replay Tests

Use Temporal's replay functionality to debug determinism issues:

```bash
# Save workflow history to file
temporal workflow show --workflow-id {orderId} --namespace apps --output json > history.json

# Replay with test environment to debug
# See java/*/src/test/java for examples
```

---

## Monitoring

### Prometheus Metrics

Apps API exposes metrics at:
```bash
curl http://localhost:8080/actuator/prometheus
```

Key metrics:
- `temporal_workflow_execution_started_total`
- `temporal_workflow_execution_completed_total`
- `temporal_activity_execution_total`
- `temporal_activity_execution_failed_total`

### Health Checks

```bash
# Apps API
curl http://localhost:8080/actuator/health

# Temporal
temporal operator namespace list
```

---

## Key Commands

```bash
# Temporal — namespaces
temporal operator namespace list
temporal operator namespace create --namespace my-namespace

# Temporal — workflows
temporal workflow list --namespace apps
temporal workflow describe --workflow-id {orderId} --namespace apps
temporal workflow show --workflow-id {orderId} --namespace apps
temporal workflow cancel --workflow-id {orderId} --namespace apps

# Temporal — nexus
temporal operator nexus endpoint list

# Temporal — worker versioning
temporal worker deployment describe --deployment-name processing --namespace processing
temporal worker deployment set-current-version --deployment-name processing --build-id local --namespace processing

# Protocol Buffers
buf lint
buf generate
buf breaking --against '.git#branch=main'

# Maven
mvn clean install         # Build everything
mvn test                  # Run tests
mvn spring-boot:run       # Run a service directly
```
