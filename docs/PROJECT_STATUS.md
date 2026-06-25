# Temporal OMS - Project Status

**Last Updated**: 2026-02-25
**Status**: Core Services In Development - Apps & Processing Workflows Implemented

## Summary

The Temporal Order Management System is actively being developed with:
- ✅ Complete project structure for Java, Python, and Web
- ✅ Protocol Buffer schemas for Apps, Processing, Fulfillments, and shared OMS
- ✅ Java Apps service with REST API and workflow orchestration
- ✅ Java Processing service with order workflow and support team handling
- ✅ Temporal client and worker configuration
- ✅ OpenTelemetry observability (needs local collector for dev)
- ✅ CompleteOrder and ProcessOrder workflow implementations
- 📋 Risk context archived (proto definitions retained, no operational code)
- 🚧 Python Fulfillments service (scaffolded)
- 🚧 SvelteKit web frontend (scaffolded)

## What's Implemented

### ✅ Project Foundation
- [x] Directory structure for Java, Python, and Web services
- [x] asdf version management (.tool-versions)
- [x] Multi-module Maven project for Java services
- [x] Protocol Buffer schemas (buf linting and code generation)
- [x] Git workflow with proper commits

### ✅ Apps Service (Mostly Complete)
**Module**: `/java/apps/`
- [x] Maven multi-module structure (apps-api, apps-core, apps-workers)
- [x] REST API entry point (ApiApplication)
- [x] Worker entry point (WorkerApplication)
- [x] CommerceWebhookController - PUT `/api/v1/commerce-app/orders/{orderId}`
- [x] PaymentsWebhookController - POST `/api/v1/payments-app/orders`
- [x] Temporal client and worker configuration
- [x] CompleteOrder workflow interface and implementation (OrderImpl)
- [x] UpdateWithStart pattern for order + payment accumulation
- [x] Order state management with timestamp sorting
- [x] Options activity for configuration management
- [x] Search attributes for customer_id
- [x] Protobuf JSON message conversion for REST
- [x] OpenAPI/Swagger documentation setup
- [ ] API key authentication (noted for later)
- [ ] Nexus service to Processing (partially wired)
- [ ] Unit tests with TestWorkflowEnvironment

### ✅ Processing Service (In Development)
**Module**: `/java/processing/`
- [x] Maven multi-module structure (processing-api, processing-core, processing-workers)
- [x] Worker entry point (WorkerApplication)
- [x] ProcessingImpl workflow orchestration
- [x] OrderImpl - Order processing workflow (Entity pattern)
- [x] CommerceAppImpl - Validate order activity interface
- [x] EnrichmentsImpl - Order enrichment workflow
- [x] FulfillmentsImpl - Order fulfillment workflow
- [x] SupportTeamImpl - Manual validation workflow
- [x] Support - Support queue interface
- [x] Nexus service stubs to Apps and Fulfillments
- [x] Order validation with manual correction support
- [x] Async activity completion for support tickets
- [ ] PIMS enrichment activity (commented as TODO)
- [ ] Payment validation activity
- [ ] Fulfillment activity
- [ ] Rate limiter for external APIs
- [ ] Unit tests

### ✅ Configuration
- [x] Temporal namespaces config (`config/temporal.yaml`)
- [x] Apps service config (`java/apps/apps-api/src/main/resources/application.yaml`)
- [x] Processing service config
- [x] Environment-specific configs (local/dev/prod)
- [x] OMS shared configuration (acme.oms.yaml)

### 🚧 Python Fulfillments Service
**Directory**: `/python/fulfillments/`
- [x] Basic scaffolding
- [ ] pyproject.toml with Poetry configuration
- [ ] Worker application entry point
- [ ] OrderFulfillmentWorkflow implementation
- [ ] Activities for shipping, inventory, and Kafka output
- [ ] Pydantic models for type safety

### 🚧 SvelteKit Web Frontend
**Directory**: `/web/`
- [x] Basic scaffolding with node_modules
- [x] SvelteKit setup
- [ ] Shopping cart functionality
- [ ] Stripe payment integration
- [ ] Order tracking with SSE
- [ ] Customer dashboard

### 🚧 Kubernetes Deployment
**Directory**: `/k8s/`
- [x] Base configuration structure
- [x] Apps service manifests
- [x] Processing service manifests
- [x] Overlays for environments
- [x] Web frontend manifests
- [ ] Fulfillments service manifests
- [ ] ConfigMaps and Secrets setup
- [ ] Temporal server Helm configuration
- [ ] Ingress configuration
- [ ] Risk k8s manifests (marked for removal)

## Known Issues & TODOs

### Immediate (Blocking)
1. **OpenTelemetry Configuration**
   - Dev runtime error: `Failed to connect to localhost:4317`
   - **Solution**: Disable OTEL with `otel.sdk.disabled: true` in application.yaml OR start OTEL collector
   - Status: Not a code issue, just local dev config

### Short Term
1. **Risk Module Cleanup**
   - [x] Removed from Java (/java/risk deleted)
   - [x] Removed from pom.xml
   - [ ] Remove from `/k8s/risk/`
   - [ ] Remove from `/proto/acme/risk/`
   - [ ] Remove from `/domain/risk/`
   - [ ] Update Temporal config to remove risk namespace

2. **Nexus Service Integration**
   - Apps → Processing: Partially wired
   - Processing → Fulfillments: Stub references
   - Need to implement actual async service calls

3. **Processing Service Activities**
   - Validate order logic (framework in place, logic TODO)
   - Enrichment API integration
   - Payment validation
   - Fulfillment initiation

4. **Python Fulfillments**
   - Basic project setup needed
   - AI Agent workflow with Pydantic

5. **Web Frontend**
   - React to completed orders
   - Implement shopping flow
   - Stripe integration

### Testing
- [ ] Unit tests for all workflows
- [ ] Replay tests for determinism
- [ ] Integration tests (e2e order flow)
- [ ] Load tests

## Architecture

### Bounded Contexts (3 active)
1. **Apps** - Order orchestration and data collection
2. **Processing** - Order validation, enrichment, fulfillment
3. **Fulfillments** (Python) - Shipping optimization and output

*Note: Risk context archived (proto definitions kept, no operational code or k8s manifests)*

### Key Patterns
- **Entity Pattern** - Workflows as domain entities (Order in each context)
- **Application Service** - CompleteOrder in Apps orchestrates the flow
- **UpdateWithStart** - Accumulate data before processing
- **Nexus** - Cross-namespace communication
- **Async Activity** - Support team manual correction with async completion

### Data Flow
```
Commerce Webhook → Apps API → CompleteOrder (submitOrder)
Payments Webhook → Apps API → CompleteOrder (capturePayment)
                  ↓
          Processing Service (Nexus)
          ├→ Validate Order (Activity)
          ├→ Enrich Order (Activity)
          └→ Fulfill Order (Activity)
                  ↓
          Fulfillments Service (Nexus - Python)
          ├→ Find Optimal Shipping (Activity)
          ├→ Allocate Inventory (Activity)
          └→ Publish to Kafka (Activity)
```

## Files & Metrics

### Java Implementation
- **Modules**: 4 (apps, processing, oms, generated)
- **Workflows**: 6+ (CompleteOrder, ProcessOrder, Enrichments, Fulfillments, Support, SupportTeam)
- **Activities**: 8+ (Options, CommerceApp, Enrichments, Fulfillments, Support)
- **Controllers**: 2 (CommerceWebhook, PaymentsWebhook)

### Protobuf Schemas
- **Active**: acme/apps, acme/processing, acme/fulfillments, acme/oms, acme/common
- **Archived**: acme/risk (proto definitions kept, no operational implementation)

### Configuration
- Temporal: 1 config file with 3 namespaces (apps, processing, removed: risk)
- Applications: 3 (apps-api, processing-workers, need: fulfillments)

## Next Steps (Priority Order)

### Priority 1 - Fix Dev Environment
1. Disable OpenTelemetry for local dev
   ```yaml
   otel.sdk.disabled: true
   ```
2. Or start OpenTelemetry collector
   ```bash
   docker run -p 4317:4317 otel/opentelemetry-collector:latest
   ```

### Priority 2 - Clean Up Risk Operational References
1. Delete `/k8s/risk/` (Kubernetes manifests)
2. Delete `/domain/risk/` (domain documentation)
3. Update `config/temporal.yaml` to remove risk namespace definition
4. Update `k8s/configmap.yaml` to remove TEMPORAL_NAMESPACE_RISK variables
5. Remove risk references from `/proto/acme/oms/v1/message.proto` (BoundedContextConfig)
- **Note**: Keep `/proto/acme/risk/` proto definitions for potential future use

### Priority 3 - Complete Apps Service
1. Implement Nexus call to Processing service
2. Add API key authentication
3. Write unit tests
4. Wire up state management for processed orders

### Priority 4 - Complete Processing Service
1. Implement validate order activity logic
2. Implement enrichment activity
3. Implement payment validation
4. Implement fulfillment initiation via Nexus

### Priority 5 - Python & Frontend
1. Setup fulfillments pyproject.toml
2. Implement fulfillment workflow and activities
3. Web frontend shopping flow
4. Stripe integration

## Development Commands

### Build Java
```bash
cd java && mvn clean install
```

### Run Apps API
```bash
mvn spring-boot:run -pl apps/apps-api
```

### Run Processing Worker
```bash
mvn spring-boot:run -pl processing/processing-workers
```

### Generate Protocol Buffers
```bash
cd proto && buf generate
```

### View Recent Commits
```bash
git log --oneline -10
```

## Success Criteria

- [x] Core Java services structured and partially implemented
- [x] Order orchestration workflow (Apps) functional
- [x] Order processing workflow (Processing) with manual validation
- [ ] Complete end-to-end order flow (Apps → Processing → Fulfillments)
- [ ] Python fulfillments service implemented
- [ ] Web frontend operational with shopping and checkout
- [ ] All tests passing
- [ ] Deployed to Minikube successfully
- [ ] Clean up all Risk references from codebase

---

**Current Branch**: feat-submit-order
**Last Significant Change**: Risk module removed, Order state management improved with timestamp sorting

See individual service READMEs for more details:
- `/domain/apps/README.md` - Apps bounded context
- `/domain/processing/README.md` - Processing bounded context
- `/python/fulfillments/README.md` - Fulfillments service
