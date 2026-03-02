# Getting Started with Temporal OMS

A Java-based Order Management System powered by Temporal workflows.

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

5. **Docker** (for local Temporal server)
   ```bash
   docker --version
   docker-compose --version
   ```

### Step 1: Start Local Temporal

Create `docker-compose.yaml` in project root:

```yaml
version: '3.8'
services:
  temporal:
    image: temporalio/auto-setup:latest
    ports:
      - "7233:7233"  # gRPC
      - "8233:8233"  # UI
    environment:
      DB: sqlite
    healthcheck:
      test: ["CMD", "temporal", "operator", "namespace", "list"]
      interval: 5s
      timeout: 5s
      retries: 5
```

Start it:
```bash
docker-compose up -d

# Wait for it to be ready
docker-compose ps
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
# Make the setup script executable
chmod +x scripts/setup-temporal-namespaces.sh

# Run it
./scripts/setup-temporal-namespaces.sh
```

This creates:
- ✅ `apps` namespace - Order orchestration and data collection
- ✅ `processing` namespace - Order validation, enrichment, fulfillment
- ✅ Nexus endpoints for Apps → Processing communication

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

# Or build specific service
cd apps && mvn clean package
cd ../processing && mvn clean package
```

This creates:
- `java/apps/apps-api/target/apps-api-1.0.0-SNAPSHOT.jar` - REST API
- `java/apps/apps-workers/target/apps-workers-1.0.0-SNAPSHOT.jar` - Apps Worker
- `java/processing/processing-workers/target/processing-workers-1.0.0-SNAPSHOT.jar` - Processing Worker

### Step 4: Run Services (6 Terminals)

**Terminal 1 - Apps REST API** (localhost:8080):
```bash
cd java/apps/apps-api
mvn spring-boot:run
```

**Terminal 2 - Apps Worker**:
```bash
cd java/apps/apps-workers
export TEMPORAL_NAMESPACE=apps
mvn spring-boot:run
```

**Terminal 3 - Processing Worker**:
```bash
cd java/processing/processing-workers
export TEMPORAL_NAMESPACE=processing
mvn spring-boot:run
```

**Terminal 4 - Temporal UI** (localhost:8233):
```bash
# Just open in browser - already running via docker-compose
open http://localhost:8233
```

All services are now ready! You should see:
- ✅ Apps API running on `http://localhost:8080`
- ✅ Apps Worker connected to `apps` namespace
- ✅ Processing Worker connected to `processing` namespace
- ✅ Temporal UI showing both namespaces

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

## Development Workflow

### Modifying Protocol Buffers

When you change `.proto` files:

```bash
cd proto

# Check for errors
buf lint

# Check for breaking changes (optional)
buf breaking --against '.git#branch=main'

# Generate code for all languages
buf generate

# This regenerates:
# - java/generated/ (Java classes)
# - python/generated/ (Python stubs)
# - web/src/lib/generated/ (TypeScript)
```

Then rebuild Java services:
```bash
cd java
mvn clean install
```

### Making Changes to Workflows

1. Edit workflow implementation in `java/apps/apps-core/src/main/java/.../OrderImpl.java`
2. Rebuild: `mvn clean package`
3. Restart the worker terminal (Ctrl+C, then re-run)
4. New workflow instances use updated code

### Adding New Activities

1. Define interface in `*-core/src/main/java/...Activities.java`
2. Implement in `*-core/src/main/java/.../ActivitiesImpl.java`
3. Register in worker configuration
4. Call from workflow

### Testing Workflows

```bash
cd java

# Run all tests
mvn test

# Run specific test
mvn test -Dtest=OrderImplTest

# Run with debug logging
mvn test -Dlogging.level.io.temporal=DEBUG
```

## Debugging

### Enable Debug Logging

Create or update `java/apps/apps-api/src/main/resources/application.yaml`:

```yaml
logging:
  level:
    root: INFO
    com.acme: DEBUG
    io.temporal: DEBUG
```

Restart the service to see debug output.

### View Workflow History

```bash
# Via Temporal UI
open http://localhost:8233/namespaces/apps/workflows/{orderId}

# Via CLI - show all events
temporal workflow show --workflow-id {orderId} --namespace apps

# Via CLI - describe current state
temporal workflow describe --workflow-id {orderId} --namespace apps

# Via CLI - query workflow state
temporal workflow query \
  --workflow-id {orderId} \
  --namespace apps \
  --type getState
```

### Replay Tests

Use Temporal's replay functionality to debug determinism issues:

```bash
# Get workflow history from UI or CLI, save as JSON
temporal workflow show --workflow-id {orderId} --namespace apps --output json > history.json

# Replay with test environment to debug
# See java/*/src/test/java for examples
```

## Troubleshooting

### ❌ "Failed to connect to localhost:4317" (OpenTelemetry Error)

This is expected in development. OpenTelemetry is trying to send metrics but there's no collector.

**Fix option 1** - Disable OpenTelemetry:
```yaml
# In application.yaml
otel.sdk.disabled: true
```

**Fix option 2** - Start OpenTelemetry collector:
```bash
docker run -p 4317:4317 otel/opentelemetry-collector:latest
```

### ❌ "Connection refused" on API calls

**Check**:
```bash
# Is Apps API running?
curl http://localhost:8080/actuator/health

# Is Temporal server running?
temporal operator namespace list
```

### ❌ "Workflow not found" on temporal commands

**Check**:
```bash
# Is worker running in correct namespace?
temporal workflow list --namespace apps

# Did you run the setup script?
./scripts/setup-temporal-namespaces.sh
```

### ❌ Workflows aren't processing orders

**Check**:
1. Both Apps and Processing workers are running
2. Both namespaces exist: `temporal operator namespace list`
3. Nexus endpoints are registered: `temporal operator nexus endpoint list`
4. Order ID doesn't contain "invalid" (that's a special test case)

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
├── oms/                        # Shared config
└── generated/                 # Generated protobuf code

scripts/
├── scenarios/                 # Customer demo scripts
└── setup-temporal-namespaces.sh
```

## Architecture Overview

### Apps Namespace
- **CompleteOrder Workflow** - Orchestrates order from start to finish
- **Updates** - Handles incoming order and payment data
- **Nexus Calls** - Forwards complete order to Processing

### Processing Namespace
- **ProcessOrder Workflow** - Validates, enriches, fulfills order
- **SupportTeam Workflow** - Handles manual corrections for invalid orders
- **Activities** - Validation, enrichment, fulfillment logic

### Communication
- **UpdateWithStart** - Apps accumulates commerce + payment data atomically
- **Nexus** - Apps initiates ProcessOrder in Processing namespace
- **Async Activities** - Support team can correct orders without blocking

## Key Commands

```bash
# Temporal namespaces
temporal operator namespace list
temporal operator namespace create --namespace my-namespace

# Workflows
temporal workflow list --namespace apps
temporal workflow describe --workflow-id {orderId} --namespace apps
temporal workflow show --workflow-id {orderId} --namespace apps
temporal workflow cancel --workflow-id {orderId} --namespace apps

# Nexus endpoints
temporal operator nexus endpoint list
temporal operator nexus endpoint create --name my-endpoint --target-namespace my-namespace --target-task-queue my-queue

# Local development
docker-compose up -d      # Start Temporal
docker-compose down       # Stop Temporal
docker-compose logs -f    # View logs

# Protocol Buffers
buf lint                  # Check for errors
buf generate              # Regenerate code from .proto files
buf breaking --against '.git#branch=main'  # Check for breaking changes

# Maven
mvn clean install         # Build everything
mvn test                  # Run tests
mvn spring-boot:run       # Run service directly
```

## Monitoring

### Prometheus Metrics

Apps API exposes metrics at:
```bash
curl http://localhost:8080/actuator/prometheus
```

Key metrics:
- `temporal_workflow_execution_started_total` - Workflows started
- `temporal_workflow_execution_completed_total` - Workflows completed
- `temporal_activity_execution_total` - Activities executed
- `temporal_activity_execution_failed_total` - Failed activities

### Health Checks

```bash
# Apps API
curl http://localhost:8080/actuator/health

# Temporal
temporal operator namespace list
```

## Next Steps

1. ✅ Run the valid order scenario from `scripts/scenarios/valid-order/`
2. ✅ Run the invalid order scenario to see manual corrections
3. ✅ Observe workflows in Temporal UI at http://localhost:8233
4. ✅ Modify a workflow and restart the worker
5. ✅ Check metrics at http://localhost:8080/actuator/prometheus

## Resources

- **[Temporal Documentation](https://docs.temporal.io/)** - Complete SDK docs
- **[PROJECT_STATUS.md](./PROJECT_STATUS.md)** - Current implementation status
- **[domain/apps/README.md](./domain/apps/README.md)** - Apps context details
- **[domain/processing/README.md](./domain/processing/README.md)** - Processing context details
- **[scripts/scenarios/README.md](./scripts/scenarios/README.md)** - Demo scenarios

## Support

Having issues?

1. Check service health: `curl http://localhost:8080/actuator/health`
2. Check Temporal: `temporal operator namespace list`
3. View logs in terminal where service is running
4. Check Temporal UI: http://localhost:8233
5. Enable debug logging in `application.yaml`