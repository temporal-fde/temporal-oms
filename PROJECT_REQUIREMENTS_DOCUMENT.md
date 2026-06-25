# Order Management System (OMS) — Project Requirements

## Overview

This repository contains a reference implementation of an Order Management System (OMS) for a clothing retailer, built progressively with Temporal. The project serves as the foundation for workshops that demonstrate how a real-world Temporal application evolves as requirements compound in complexity.

Orders flow through three phases:

| Phase | Description |
|---|---|
| **Capture** | Collect order information from Commerce App and Payment Processor |
| **Processing** | Validate, enrich, and coordinate order data across downstream services |
| **Fulfillment** | Allocate inventory and complete shipping |

---

## Project Evolution

The workshops follow this application through two major versions, each introducing a new layer of Temporal capabilities.

### v1 — Order Processing

**[PRD: OMS Order Processing](docs/prd-v1-order-processing.md)**

The initial scope targets the **Processing** phase. The existing system uses a fragile Kafka-based chain of consumers to validate, enrich, and coordinate orders. Temporal replaces this with a durable workflow that:

- Aggregates inputs arriving out-of-order and at unpredictable times
- Enforces a 30-day TTL with automatic expiration writes to the customer dashboard
- Validates order data against the Commerce App API (rate-limited at 150 RPS)
- Enriches items via the Product Information Management System
- Waits up to 30 days for Payment Capture, cancelling if it never arrives
- Supports order cancellation up to the point of payment capture
- Outputs an enriched Order payload to the `order-fulfillment` Kafka topic

**Key Temporal concepts**: Signals, timers, activities, rate limiting, human-in-the-loop (HitL), workflow versioning for vNext risk collection.

### v2 — Smart Fulfillment

**[PRD: OMS Smart Fulfillment](docs/prd-v2-smart-fulfillment.md)**

The second scope replaces the legacy Kafka-based fulfillment consumer with a **Temporal Smart Fulfillment Workflow** powered by an LLM Shipping Agent. Where v1 dropped a message on a Kafka topic and walked away, v2 owns the fulfillment process end-to-end:

- Re-validates shipping rates at fulfillment time to protect business margins
- Uses an LLM Shipping Agent to re-shop carriers when rates have spiked
- Accounts for real-world supply chain disruptions (weather, infrastructure events)
- Manages inventory allocation, label generation, and delivery tracking
- Fires margin leakage alerts when no cost-neutral carrier option is available
- Waits for carrier delivery confirmation via Signals before completing

**Key Temporal concepts**: Nexus operations, `UpdateWithStart`, child workflows, LLM agent integration, workflow pinning and draining.

---

## v1 → v2: What Changed

In v1, the Processing phase was rebuilt with Temporal but the downstream fulfillment still consumed from a Kafka topic using a simple, deterministic consumer. This worked, but left fulfillment brittle: stale shipping quotes ate margins, carrier exceptions required manual triage, and supply chain disruptions weren't accounted for at dispatch time.

v2 replaces that consumer with a `fulfillment.Order` Temporal Workflow started via Nexus. The `apps.Order` workflow from v1 now kicks off the fulfillment workflow immediately at order creation (suspended until processing completes), then signals it to begin fulfillment once the order is processed. The LLM Shipping Agent handles the non-deterministic, real-world reasoning that a static workflow cannot.

---

## Evaluation Criteria

Both versions are designed to demonstrate the "ilities" of a production Temporal application:

- Use of Temporal primitives
- Completeness
- Extensibility and maintainability to support subsequent versions
- Test strategy
- Cohesive failure strategy
- Integration considerations that impact scalability
