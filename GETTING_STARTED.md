# Getting Started with Temporal OMS

A Java-based Order Management System powered by Temporal workflows.

## Choose Your Setup Path

### 🎯 Want to Deploy to Kubernetes?

If you want to run the full application stack in Kubernetes (either locally via KinD or with Temporal Cloud), see **[DEPLOYMENT.md](DEPLOYMENT.md)** for:
- One-liner deployment with `./scripts/demo-up.sh`
- Support for both local Temporal and Temporal Cloud
- Production-like Kubernetes environment
- Traefik ingress for API access

### 🏃 Want to Run Locally First?

Continue below for pure local development without Kubernetes. This is great for:
- Quick iteration on code
- Understanding the architecture
- Running workflows directly on your machine

---

## Quick Start

### Prerequisites

1. **Java 21+**
   ```bash
   # Install with asdf (recommended)
   asdf install  # Uses .tool-versions

   # Or install manually
   java --version  # Must be 21+
   ```

2. **Maven 3.9+**
   ```bash
   mvn --version
   ```

3. **Temporal CLI**
   ```bash
   # macOS
   brew install temporal

   # Or from: https://github.com/temporalio/cli/releases
   temporal --version
   ```

4. **HTTP Client (xh or curl)**
   ```bash
   # macOS with xh (recommended - cleaner syntax)
   brew install xh

   # Or use curl (included on all systems)
   curl --version
   ```

5. **uv** (Python package manager, for the Python fulfillment worker)
   ```bash
   # macOS
   brew install uv

   # Or: curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install Python dependencies (run once from repo root)
   cd python && uv sync
   ```

### Configure Environment

Copy the environment template before starting any services:

```bash
cp .env.example .env.local
```

All Java services and Python workers load `.env.local` automatically — no extra steps needed once it exists. The defaults in `.env.example` are already correct for local Temporal (no API keys required for Temporal itself).

API keys are only needed for integration features. Workers start and connect without them — activities that call external APIs will fail with a clear error message if the key is missing when that feature is exercised.

| Variable | Where to get it | Needed for |
|----------|----------------|------------|
| `EASYPOST_API_KEY` | [easypost.com](https://www.easypost.com) → Dashboard → API Keys | Address verification, carrier rate quotes |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | AI shipping agent (shipping route selection) |
| `PREDICTHQ_API_KEY` | [predicthq.com](https://www.predicthq.com) | Location risk events (weather/event disruption data) |

### Step 1: Start Local Temporal

```bash
temporal server start-dev
```

Verify Temporal is running:
```bash
# Visit UI
open http://localhost:8233

# Or check with CLI
temporal operator namespace list
```

### Step 2: Setup Temporal Namespaces

Create Temporal namespaces and Nexus endpoints for cross-namespace communication:

```bash
./scripts/setup-temporal-namespaces.sh
```

This creates:
- ✅ `apps` namespace — Order orchestration and data collection
- ✅ `processing` namespace — Order validation, enrichment, fulfillment
- ✅ `fulfillment` namespace — Order fulfillment
- ✅ Nexus endpoints for Apps → Processing communication
- ✅ Sets the current worker version for the `processing` deployment

> **Why `set-current-version`?** The workers in this project run with Worker Versioning enabled (`deployment-properties` in their config). When versioning is active, Temporal tracks each deployment by build-id and only routes tasks to a version that has been explicitly set as the "current" version. Until that happens, workers will connect and poll successfully — but the server will not dispatch any tasks to them, and Nexus calls into `processing` will silently stall.
>
> The script calls this on your behalf:
> ```bash
> temporal worker deployment set-current-version \
>   --deployment-name processing \
>   --build-id local \
>   --allow-no-pollers \
>   --namespace processing
> ```
> The `--allow-no-pollers` flag lets you set the version before the workers have started. Once workers come up and poll, they see themselves as the current version and tasks flow normally.
>
> **This is different from Levels 2 and 3 (Kubernetes).** When the Temporal Worker Controller is present, `set-current-version` is called automatically — the controller waits for pollers to appear on a new build-id and then promotes that version itself. You never run it manually. See [DEPLOYMENT.md](DEPLOYMENT.md) for details.

Verify setup:
```bash
temporal operator namespace list
temporal operator nexus endpoint list
```

### Step 3: Build Java Services

```bash
cd java

# Build all modules
mvn clean install -DskipTests
```

This creates:
- `java/apps/apps-api/target/apps-api-1.0.0-SNAPSHOT.jar` — REST API
- `java/apps/apps-workers/target/apps-workers-1.0.0-SNAPSHOT.jar` — Apps Worker
- `java/processing/processing-workers/target/processing-workers-1.0.0-SNAPSHOT.jar` — Processing Worker

### Step 4: Run Services

**Terminal 1 — Apps REST API** (localhost:8080):
```bash
cd java/apps/apps-api
mvn spring-boot:run
```

**Terminal 2 — Apps Worker**:
```bash
cd java/apps/apps-workers
mvn spring-boot:run
```

**Terminal 3 — Processing Worker**:
```bash
cd java/processing/processing-workers
mvn spring-boot:run
```

**Terminal 4 — Fulfillment Worker** (Java):
```bash
cd java/fulfillment/fulfillment-workers
mvn spring-boot:run
```

> Uses `EASYPOST_API_KEY` from `.env.local` for address verification. The worker starts without it, but address verification activities will fail with a clear error until the key is set.

**Terminal 5 — Python Fulfillment Workers** (shipping agent + EasyPost + PredictHQ):
```bash
cd python/fulfillment
uv run --project .. python -m src.worker
```

> Uses `ANTHROPIC_API_KEY`, `EASYPOST_API_KEY`, and `PREDICTHQ_API_KEY` from `.env.local`. Workers connect and poll without them — activities that call these APIs surface a clear error when invoked without the key.

All services are now ready:
- ✅ Apps API running on `http://localhost:8080`
- ✅ Apps Worker connected to `apps` namespace
- ✅ Processing Worker connected to `processing` namespace
- ✅ Fulfillment Worker connected to `fulfillment` namespace
- ✅ Python Workers (shipping agent, EasyPost, PredictHQ) connected to `fulfillment` namespace
- ✅ Temporal UI at `http://localhost:8233`

---

## Demo Scenarios

Once services are running, try the customer demo scenarios:

```bash
cd scripts/scenarios

# Valid order (happy path)
cd valid-order
./1-submit-order.sh
./2-capture-payment.sh

# Invalid order (manual correction)
cd ../invalid-order
./1-submit-order.sh
./2-capture-payment.sh
./3-complete-validation.sh

# Order cancellation
cd ../cancel-order
./1-submit-order.sh
./2-cancel-order.sh
```

See `scripts/scenarios/README.md` for detailed demo instructions and talking points.

---

## Review Orders Sent for Fulfillment
To view orders sent to Kafka for fulfillment, navigate to:

`http://localhost:8071/admin/order-fulfillment/<orderId>`

For example, the order fulfillment message created by the "Valid order (happy path)" scripts can be viewed by navigating to:

`http://localhost:8071/admin/order-fulfillment/valid-order-123`

**Note:**
This is only for demonstration purposes and not for production. It shows the fulfillment message was added to the Kafka topic.  At this time, it is only available when running the application locally (Level 1 - No Kubernetes, No Cloud).  
---

## API Endpoints

### Submit Order
```bash
xh PUT http://localhost:8080/api/v1/commerce-app/orders/{orderId} \
  customerId="cust-001" \
  order:='{"orderId":"...","items":[...],"shippingAddress":{...}}'
```

### Capture Payment
```bash
xh POST http://localhost:8080/api/v1/payments-app/orders \
  customerId="cust-001" \
  rrn="payment-intent-123" \
  amountCents=9999 \
  metadata:='{"orderId":"..."}'
```

### Check Order Status
```bash
# Via Temporal UI
open http://localhost:8233/namespaces/apps/workflows/{orderId}

# Or via CLI
temporal workflow describe \
  --workflow-id {orderId} \
  --namespace apps
```

---

## Project Structure

```
java/
├── apps/
│   ├── apps-api/              # REST API server (port 8080)
│   ├── apps-core/             # Workflows & activities
│   └── apps-workers/          # Worker process
├── processing/
│   ├── processing-core/       # Workflows & activities
│   └── processing-workers/    # Worker process
├── oms/                       # Shared config
└── generated/                 # Generated protobuf code

scripts/
├── scenarios/                 # Customer demo scripts
└── setup-temporal-namespaces.sh
```

---

## Architecture Overview

### Apps Namespace
- **CompleteOrder Workflow** — Orchestrates order from start to finish
- **Updates** — Handles incoming order and payment data
- **Nexus Calls** — Forwards complete order to Processing

### Processing Namespace
- **ProcessOrder Workflow** — Validates, enriches, fulfills order
- **SupportTeam Workflow** — Handles manual corrections for invalid orders
- **Activities** — Validation, enrichment, fulfillment logic

### Communication
- **UpdateWithStart** — Apps accumulates commerce + payment data atomically
- **Nexus** — Apps initiates ProcessOrder in Processing namespace
- **Async Activities** — Support team can correct orders without blocking

---

## Troubleshooting

### ❌ `INVALID_ARGUMENT: versioning behavior cannot be specified without deployment options`

This error means a worker registered a workflow type with a `@WorkflowVersioningBehavior` annotation but the worker itself does not have `deployment-properties` (i.e. `use-versioning: true`) configured.

The `@WorkflowVersioningBehavior` annotation is compiled into the workflow type registration and is always sent to the server — it cannot be disabled via Spring config or environment variables. If the worker config doesn't declare a deployment, the server rejects it.

**Fix**: Ensure the worker running this workflow has `deployment-properties.use-versioning: true` in its config, and that a current version has been set for that deployment.

### ❌ "Failed to connect to localhost:4317" (OpenTelemetry Error)

This is expected in development. OpenTelemetry is trying to send metrics but there's no collector.

**Fix option 1** — Disable OpenTelemetry:
```yaml
# In application.yaml
otel.sdk.disabled: true
```

**Fix option 2** — Start OpenTelemetry collector:
```bash
docker run -p 4317:4317 otel/opentelemetry-collector:latest
```

### ❌ "Connection refused" on API calls

```bash
# Is Apps API running?
curl http://localhost:8080/actuator/health

# Is Temporal server running?
temporal operator namespace list
```

### ❌ "Workflow not found" on temporal commands

```bash
# Is worker running in correct namespace?
temporal workflow list --namespace apps

# Did you run the setup script?
./scripts/setup-temporal-namespaces.sh
```

### ❌ Workflows aren't processing orders

1. Both Apps and Processing workers are running
2. Both namespaces exist: `temporal operator namespace list`
3. Nexus endpoints are registered: `temporal operator nexus endpoint list`
4. Order ID doesn't contain "invalid" (that's a special test case)

### ❌ Workers are connected but orders never progress (tasks not dispatched)

This is the Worker Versioning routing problem. Workers with `deployment-properties` configured will connect and poll successfully but receive no tasks if a current version has not been set.

**Fix**: Re-run the setup script (it is idempotent):
```bash
./scripts/setup-temporal-namespaces.sh
```

Or set the version directly:
```bash
temporal worker deployment set-current-version \
  --deployment-name processing \
  --build-id local \
  --allow-no-pollers \
  --namespace processing
```

Verify the current version is set:
```bash
temporal worker deployment describe \
  --deployment-name processing \
  --namespace processing
```

---

## Next Steps

1. ✅ Run the valid order scenario from `scripts/scenarios/valid-order/`
2. ✅ Run the invalid order scenario to see manual corrections
3. ✅ Observe workflows in Temporal UI at http://localhost:8233
4. ✅ Modify a workflow and restart the worker — see [DEVELOPMENT.md](DEVELOPMENT.md)
5. ✅ Deploy to Kubernetes — see [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Resources

- **[DEVELOPMENT.md](DEVELOPMENT.md)** — Protocol Buffers, workflow changes, debugging, testing
- **[DEPLOYMENT.md](DEPLOYMENT.md)** — Kubernetes deployment (KinD + Temporal Cloud)
- **[Temporal Documentation](https://docs.temporal.io/)** — Complete SDK docs
- **[domain/apps/README.md](./domain/apps/README.md)** — Apps context details
- **[domain/processing/README.md](./domain/processing/README.md)** — Processing context details
- **[scripts/scenarios/README.md](./scripts/scenarios/README.md)** — Demo scenarios
