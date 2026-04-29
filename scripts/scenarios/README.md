# Order Processing Scenarios

Executable demo scripts for showcasing the Temporal Order Management System to customers.

Each scenario is a standalone workflow that demonstrates different order processing paths.

Every scenario run uses a unique generated order/workflow ID and a matching
unique customer ID. Step 1 stores the current run context under
`${TMPDIR:-/tmp}/fde-temporal-oms-scenarios`, and later steps in the same
scenario read that context automatically. To force specific IDs, run a script
with `ORDER_ID=...` and/or `CUSTOMER_ID=...`.

## Prerequisites

- ✅ Temporal Server running (localhost:7233)
- ✅ Apps API server running (localhost:8080)
- ✅ Processing API server running (localhost:8070)
- ✅ Processing Workers running
- ✅ `xh` (HTTP client) installed
- ✅ `temporal` CLI installed

## Scenarios

### 1. Valid Order (Happy Path) ✓
**Directory**: `valid-order/`

Demonstrates an order that passes all validation and proceeds through the complete workflow automatically.

```bash
cd valid-order
./run.sh                   # Prompts before each step
./run.sh --yes             # Runs all steps with short pauses
./1-submit-order.sh        # Submit valid order with a fresh generated ID
./2-capture-payment.sh     # Uses the ID from the latest submit step
```

**What happens:**
1. Order submitted to Apps service
2. Payment captured automatically
3. Order passes validation in Processing service
4. Order is enriched (inventory/SKU lookup)
5. Order moves to fulfillment

---

### 2. Invalid Order with Manual Correction ⚠️
**Directory**: `invalid-order/`

Demonstrates an order that fails validation and requires manual support team intervention to be corrected.

```bash
cd invalid-order
./run.sh                      # Prompts before each step
./run.sh --yes                # Runs all steps with short pauses
./1-submit-order.sh           # Submit invalid order with a fresh generated ID
./2-capture-payment.sh        # Uses the ID from the latest submit step
./3-complete-validation.sh    # Uses the same ID and resumes processing
```

**What happens:**
1. Order submitted to Apps service (will fail validation)
2. Payment captured, order processing begins
3. Validation fails in Processing service
4. Order goes into manual review queue
5. Support team reviews and provides corrections
6. Workflow resumes with corrected data

**Note**: Generated IDs for this scenario start with `invalid-order`, which contains `invalid` and triggers validation failure. This demonstrates the support workflow.

---

### 3. Order Cancellation ❌
**Directory**: `cancel-order/`

Demonstrates canceling an order before it completes processing.

```bash
cd cancel-order
./run.sh                 # Prompts before each step
./run.sh --yes           # Runs all steps with short pauses
./1-submit-order.sh      # Submit order with a fresh generated ID
./2-cancel-order.sh      # Uses the same ID and cancels mid-flight
```

**What happens:**
1. Order submitted to Apps service
2. Cancellation request sent via workflow update
3. Order processing is aborted
4. Workflow completes in canceled state

---

### 4. Margin Spike
**Directory**: `margin-spike/`

Demonstrates the ShippingAgent alternate-warehouse path when customer paid price is intentionally too low.

```bash
cd margin-spike
./run.sh                 # Prompts before each step
./run.sh --yes           # Runs all steps with short pauses
./1-submit-order.sh      # Submit order with a fresh generated ID
./2-capture-payment.sh   # Uses the same ID and triggers processing
```

**What happens:**
1. Order submitted with `paidPriceCents=1`
2. Payment captured
3. ShippingAgent fetches fixture-backed rates
4. ShippingAgent calls `find_alternate_warehouse`
5. Recommendation finalizes with `MARGIN_SPIKE`

---

### 5. SLA Breach
**Directory**: `sla-breach/`

Demonstrates the ShippingAgent SLA breach path using an explicit same-day delivery requirement.

```bash
cd sla-breach
./run.sh                 # Prompts before each step
./run.sh --yes           # Runs all steps with short pauses
./1-submit-order.sh      # Submit order with a fresh generated ID
./2-capture-payment.sh   # Uses the same ID and triggers processing
```

**What happens:**
1. Order submitted with `deliveryDays=0`
2. Payment captured
3. ShippingAgent fetches fixture-backed rates
4. ShippingAgent calls `find_alternate_warehouse`
5. Recommendation finalizes with `SLA_BREACH`

---

## Running a Demo

### Example: Run the Valid Order scenario
```bash
cd /path/to/temporal-oms/scripts/scenarios/valid-order

echo "Step 1: Submit order"
./1-submit-order.sh

# Observe in Temporal UI while talking about data collection phase
# Then proceed to payment

echo "Step 2: Capture payment and watch it flow through the system"
./2-capture-payment.sh

# Check Temporal UI for:
# - Apps CompleteOrder workflow processing the accumulated data
# - Processing namespace order validation/enrichment/fulfillment
```

### Example: Run the Invalid Order scenario
```bash
cd /path/to/temporal-oms/scripts/scenarios/invalid-order

echo "Step 1: Submit an order that will fail validation"
./1-submit-order.sh

echo "Step 2: Capture payment - triggers processing"
./2-capture-payment.sh

# At this point, show in UI that validation failed
# Orders sit in pending validation queue
# Support team (SupportTeam workflow) has async activities waiting

echo "Step 3: Support team completes validation correction"
./3-complete-validation.sh

# Show how the order continues processing after manual intervention
```

---

## Talking Points While Running Demos

### Data Accumulation (Apps Service)
- "Orders start with incomplete data - we're collecting both commerce and payment info"
- "The workflow uses UpdateWithStart pattern for atomic data collection"
- "Most recent order and payment are always available for processing"

### Validation & Support (Processing Service)
- "Once both order and payment arrive, we validate against business rules"
- "If validation fails, the order doesn't just error - it goes to human review"
- "The support team can asynchronously correct issues without blocking the system"

### Automatic Processing (Happy Path)
- "Valid orders flow completely automatically through enrichment and fulfillment"
- "No human intervention needed - deterministic and reliable"

### Durability
- "All steps are recorded - we can replay, audit, and debug any order"
- "Temporal guarantees each step executes exactly once, even on failures"

---

## Viewing State in Temporal UI

While demos are running, open [Temporal UI](http://localhost:8233) to show:

1. **Apps namespace**: CompleteOrder workflow instances
   - Watch it accumulate order + payment data
   - See state updates via Updates

2. **Processing namespace**:
   - ProcessOrder workflows handling validation/enrichment
   - SupportTeam workflows with manual validation tasks
   - Support queue growing for invalid orders

3. **Workflows**:
   - Click into specific workflows to see execution history
   - Show Workflow Input/Output at each stage
   - Demonstrate deterministic replay of failures

---

## Customizing Scenarios

Edit the scripts to change:
- **Order ID**: Set `ORDER_ID=your-id` when invoking a script or `run.sh`
- **Customer ID**: Generated uniquely by default; set `CUSTOMER_ID=your-customer` to override
- **Items**: Modify the JSON to include different products
- **Payment Amount**: Set `PAYMENT_AMOUNT_CENTS=9999` when invoking a script or `run.sh`

### Run Context

The generated values are saved outside the repository so scenario runs do not
dirty the worktree:

```bash
${TMPDIR:-/tmp}/fde-temporal-oms-scenarios/<scenario>.env
```

If a later step says no saved run context exists, run that scenario's
`1-submit-order.sh` first, use the scenario `run.sh`, or provide `ORDER_ID`
manually.

For invalid-order validation completion, the REST step retries HTTP 409 while
the support workflow is still registering the validation request. Tune this with
`VALIDATION_COMPLETE_MAX_ATTEMPTS` and `VALIDATION_COMPLETE_RETRY_SECONDS`.

---

## Troubleshooting

### "Connection refused" on xh commands
- Ensure Apps API is running on localhost:8080
- Check: `curl http://localhost:8080/actuator/health`

### "Workflow not found" on temporal commands
- Ensure Temporal Server is running
- Check: `temporal workflow list --namespace apps`

### Payment endpoint returns 409 Conflict
- Order is already processing
- Use a different order ID in the next scenario

### Support team workflow not found
- Ensure Processing Workers are running
- The SupportTeam workflow must be registered in the worker

### Validation completion returns 404
- Ensure `processing-api` is running on localhost:8070
- Check: `curl http://localhost:9081/actuator/health`
- If using a tunnel or Kubernetes ingress, set `PROCESSING_API_ENDPOINT`

---

## Next Steps After Demos

- Explain the bounded context architecture (Apps, Processing, Fulfillments)
- Show how Nexus enables cross-namespace communication
- Discuss how each context can be scaled independently
- Explain the async nature of the support workflow
