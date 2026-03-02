# Order Processing Scenarios

Executable demo scripts for showcasing the Temporal Order Management System to customers.

Each scenario is a standalone workflow that demonstrates different order processing paths.

## Prerequisites

- ✅ Temporal Server running (localhost:7233)
- ✅ Apps API server running (localhost:8080)
- ✅ Processing Workers running
- ✅ `xh` (HTTP client) installed
- ✅ `temporal` CLI installed

## Scenarios

### 1. Valid Order (Happy Path) ✓
**Directory**: `valid-order/`

Demonstrates an order that passes all validation and proceeds through the complete workflow automatically.

```bash
cd valid-order
./1-submit-order.sh        # Submit valid order
./2-capture-payment.sh     # Capture payment → auto-validates → enriches → fulfills
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
./1-submit-order.sh           # Submit invalid order
./2-capture-payment.sh        # Capture payment → triggers validation
./3-complete-validation.sh    # Support team corrects and resumes
```

**What happens:**
1. Order submitted to Apps service (will fail validation)
2. Payment captured, order processing begins
3. Validation fails in Processing service
4. Order goes into manual review queue
5. Support team reviews and provides corrections
6. Workflow resumes with corrected data

**Note**: The order ID "invalid-order-123" contains "invalid" which triggers validation failure. This demonstrates the support workflow.

---

### 3. Order Cancellation ❌
**Directory**: `cancel-order/`

Demonstrates canceling an order before it completes processing.

```bash
cd cancel-order
./1-submit-order.sh      # Submit order
./2-cancel-order.sh      # Cancel the order mid-flight
```

**What happens:**
1. Order submitted to Apps service
2. Cancellation request sent via workflow update
3. Order processing is aborted
4. Workflow completes in canceled state

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
- **Order ID**: Replace `cancel-order-123` with your own ID
- **Customer ID**: Change `cust-001` to any customer
- **Items**: Modify the JSON to include different products
- **Payment Amount**: Change `amountCents=9999` (in cents, so 9999 = $99.99)

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

---

## Next Steps After Demos

- Explain the bounded context architecture (Apps, Processing, Fulfillments)
- Show how Nexus enables cross-namespace communication
- Discuss how each context can be scaled independently
- Explain the async nature of the support workflow