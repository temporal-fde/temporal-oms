# Temporal OMS - Java Implementation

## Configuration Strategy

This project uses a **modular configuration pattern** where each bounded context (BC) shares infrastructure configuration while remaining independently deployable.

### Core Concept

1. **Shared Contracts Module** (`oms`)
   - Contains `OmsProperties` (@ConfigurationProperties) that defines OMS endpoints across all BCs
   - Defines `acme.oms.yaml` with shared `oms:` configuration
   - Auto-configures via `@AutoConfiguration` so it's available to all dependent modules

2. **Bounded Context Configuration** (`{context}-core`)
   - Each BC has `acme.{context}.yaml` that imports the shared OMS config
   - Defines Temporal connection properties (namespace, target, server settings)
   - Defines worker configuration (task queue, workflow classes, activity beans)

3. **Runnable Applications** (`{context}-api`, `{context}-workers`)
   - Minimal `application.yaml` with just a single import to the BC's config
   - All other configuration inherited from the BC module
   - Can override specific values if needed

### Configuration Import Chain

```
app (api/workers)
  ↓
app-config.yaml: spring.config.import: classpath:acme.{context}.yaml
  ↓
acme.{context}.yaml: spring.config.import: classpath:acme.oms.yaml
  ↓
acme.oms.yaml: oms: { endpoints, connections }
```

### Adding a New Bounded Context

To add a new BC (e.g., "fulfillments"):

1. **Create the module structure:**
   - `fulfillments-core` (workflows, domain logic)
   - `fulfillments-api` (REST endpoints)
   - `fulfillments-workers` (Temporal workers)

2. **In `fulfillments-core/src/main/resources/acme.fulfillments.yaml`:**
   ```yaml
   spring:
     config:
       import: classpath:acme.oms.yaml
     temporal:
       namespace: fulfillments
       connection:
         target: localhost:7233
       workers:
         - task-queue: fulfillments
           workflow-classes: [com.acme.fulfillments.workflows.FulfillmentImpl]
           activity-beans: [...]
   ```

3. **In `fulfillments-api/src/main/resources/application.yaml`:**
   ```yaml
   spring:
     config:
       import: classpath:acme.fulfillments.yaml
     application:
       name: fulfillments-api
   ```

4. **In `fulfillments-workers/src/main/resources/application.yaml`:**
   ```yaml
   spring:
     config:
       import: classpath:acme.fulfillments.yaml
     application:
       name: fulfillments-workers
   ```

5. **Update `oms/src/main/resources/acme.oms.yaml`:**
   - Add fulfillments endpoints under the `oms:` section so other BCs can reach it

### Key Principles

- **DRY**: Shared `oms:` config defined once, reused by all BCs
- **Explicit Imports**: Use `spring.config.import` (not profiles) for clarity
- **Auto-Discovery**: `@AutoConfiguration` in oms module loads configs automatically
- **Minimal Runnables**: API and worker apps have nearly identical configs—only differ by task queue settings