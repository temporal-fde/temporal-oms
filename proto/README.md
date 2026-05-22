# Proto Contracts — Ownership, Structure, and Evolutionary Design

This document describes the principles that govern how message contracts are defined, owned, and evolved across the bounded contexts in this system. It exists to prevent the most common failure mode in distributed systems: a **messaging big ball of mud**, where it becomes unclear who owns what, changes in one service silently break another, and no one can evolve their interface without negotiating with half the codebase.

---

## Bounded Contexts

The system is divided into the following bounded contexts (BCs), each with its own Temporal namespace and its own ubiquitous language:

| BC | Role | Namespace |
|----|------|-----------|
| `apps` | Application Service / Orchestrator | `apps` |
| `processing` | Domain Service — order validation and enrichment | `processing` |
| `fulfillment` | Domain Service — inventory, shipping, delivery | `fulfillment` |
| `risk` | Domain Service — fraud detection | `risk` |

Each BC owns its proto package under `acme/<bc>/`. Within that, `domain/v1/` holds workflow and activity contracts internal to the BC.

There are two shared packages that sit outside any single BC:

- `acme/oms/v1/` — OMS-level value objects (`Order`, `Payment`, `Item`) used when passing structured data through the `apps` orchestration layer
- `acme/common/v1/` — Universal value types (`Money`, `Address`, `Timestamp`) that have no business semantics and appear everywhere

> **Planned improvement — consolidate `common/v1` into `oms/v1` as the true Shared Kernel.**
>
> The split between `oms/v1` and `common/v1` is artificial. `Money`, `Address`, and `Coordinate` are OMS domain primitives — they exist because orders have prices and shipments have destinations. They are not infrastructure utilities. Similarly, `common/v1/llm.proto` defines AI agent tool-call and prompt structures that belong to the domain as agent capabilities become first-class BCs rather than incidental infrastructure.
>
> The intended end state is that `acme/oms/v1/` is the single Shared Kernel for the entire OMS domain — the one package that all BCs may freely import for primitive domain types. `acme/common/v1/` will be dissolved into it. The mechanical work (updating all proto imports and regenerating) should be batched as a dedicated breaking-change commit rather than done inline with feature work.
>
> Until that consolidation happens, treat `common/v1` as an annex of the `oms/v1` shared kernel — the same ownership and change-coordination rules apply to both.

---

## The Core Principle: Handler Owns the Contract

> The service that **handles** an operation defines the message shapes for that operation. Callers take a dependency on the handler's contracts, not the other way around.

This means:

- `fulfillment.Order` defines `FulfillOrderRequest` and `FulfillOrderResponse`
- `processing.Order` defines `ProcessOrderRequest` and `GetProcessOrderStateResponse`
- A caller that invokes `fulfillOrder` imports from `fulfillment/domain/v1/`, not from its own package

The consequence is that **handlers have no upstream dependencies**. A handler's domain proto package never imports from its callers. It imports only from shared packages (`common/v1`, `oms/v1`) and its own sibling files.

This is the inverse of what LLM-assisted coding tends to produce (callers inline the contract at the call site and pass it to the handler), and the difference matters at scale: with handler ownership, any team can evolve their interface without coordinating with upstream callers — the callers simply update their mapping code.

**References:**
- Evans, *Domain-Driven Design* (2003) — Chapter 14: Maintaining Model Integrity
- Vernon, *Implementing Domain-Driven Design* (2013) — Chapter 2: Domains, Subdomains, and Bounded Contexts
- Fowler, [Bounded Context](https://martinfowler.com/bliki/BoundedContext.html)

---

## The `apps` BC Is an Orchestrator, Not a Peer

The `apps` BC is an **Application Service** in the DDD sense: it coordinates domain services to achieve a user-visible goal (complete an order, track progress, stream events to a UI). It is not a domain service itself.

The dependency graph must always look like this:

```
apps  ──►  processing   (apps calls processing, depends on its contracts)
apps  ──►  fulfillment  (apps calls fulfillment, depends on its contracts)

processing  ✗  fulfillment   (domain services must not depend on each other)
fulfillment  ✗  processing   (domain services must not depend on each other)
```

Domain services (`processing`, `fulfillment`, `risk`) are peers. They do not call each other and they do not import from each other's proto packages. If they appear to need data from a sibling BC, that data must arrive via `apps`, which holds the full order state and coordinates the handoffs.

This keeps each domain service independently deployable and independently evolvable. A change to `processing`'s enrichment output is contained to `processing` and the mapping code in `apps` — `fulfillment` never knows it happened.

**References:**
- Evans, *Domain-Driven Design* — Chapter 14: Context Map patterns (Customer/Supplier, Conformist)
- Newman, *Building Microservices* (2021) — Chapter 4: Microservice Communication Styles
- Fowler, [Application Service](https://martinfowler.com/eaaCatalog/serviceLayer.html)

---

## The Anti-Corruption Layer: Translation Is the Orchestrator's Job

When `apps` calls `fulfillment`, it does not pass a `processing.GetProcessOrderStateResponse` wholesale into a `fulfillment.FulfillOrderRequest`. It **maps** the data: extracting the fields fulfillment cares about and constructing fulfillment's own message types.

```
processing.EnrichedItem  ──[apps maps]──►  fulfillment.FulfillmentItem
oms.Order.shipping_address  ──[apps maps]──►  fulfillment.PlacedOrder.shipping_address
```

This translation layer is called an **Anti-Corruption Layer (ACL)**. It looks like boilerplate. It is not. It is the explicit statement that two domain services speak different languages, and `apps` is the translator. Each service can evolve its own language without forcing a rename or reshape on the other.

The guiding question is: *whose language are we speaking?* In fulfillment's contract, the language is fulfillment's. In processing's contract, the language is processing's. In `apps`, the language is the user-visible order lifecycle — and `apps` translates between all of them.

> "Architecture wins, not coding." Accepting some mapping verbosity in the orchestration layer is the deliberate price of loose coupling in the domain layer.

**References:**
- Evans, *Domain-Driven Design* — Chapter 14: Anti-Corruption Layer
- Fowler, [Anti-Corruption Layer](https://martinfowler.com/bliki/AntiCorruptionLayer.html)
- Richardson, *Microservices Patterns* (2018) — Chapter 3: Inter-process communication

---

## File Conventions Within a BC

### `workflows.proto`
Holds `Request` and `Response` messages that appear in Temporal workflow method signatures — workflow inputs, update handlers, query responses, signal inputs, activity inputs and outputs, and Nexus operation contracts. Message names are derived from the operation name:

```proto
// operation: fulfillOrder
message FulfillOrderRequest { ... }
message FulfillOrderResponse { ... }

// operation: validateOrder
message ValidateOrderRequest { ... }
message ValidateOrderResponse { ... }
```

Every operation has a `Request` and a `Response`, even if the response is empty. This preserves the ability to add response fields later without changing the operation signature.

Data shapes that are embedded in operation messages but carry no operation semantics of their own also live here when they are tightly coupled to a single operation (e.g., `ProcessedOrder` is only ever a field inside `FulfillOrderRequest`). When a shape is referenced across multiple operations within the same BC, it moves to `values.proto`.

### `values.proto`
Holds reusable data shapes within a BC — value objects referenced by more than one operation message. Examples: `FulfillmentItem` (used in `HoldItemsRequest`, `ReserveItemsRequest`, `GetCarrierRatesRequest`), `ShippingSelection` (used in `FulfillOrderResponse` and `GetFulfillmentOrderStateResponse`).

`values.proto` does **not** hold operation contracts. It holds domain nouns, not verbs.

### When to elevate to `common/v1`

A type belongs in `acme/common/v1/` only if:

1. It is conceptually universal — it carries no business semantics specific to any BC (`Money`, `Address`, `Timestamp`), and
2. It appears in three or more BCs independently (not just because one BC passes it through to another)

If a shape is duplicated in two BCs, the correct response is usually to keep the duplication and let each BC own its own copy — they will diverge over time and the duplication makes that evolution safe. Premature elevation to `common/v1` creates a hidden shared kernel that everyone depends on and no one can change freely.

---

## Strangler Fig Migration: Versioning Away Old Coupling

As domain services are introduced or promoted to full Temporal namespaces, old coupling patterns get replaced incrementally. The current system is mid-migration on the fulfillment BC:

**Old pattern** (being versioned away):
```
apps.Order  ──►  processing.Order  ──[Activity→Kafka]──►  fulfillment consumer
```

**New pattern**:
```
apps.Order  ──►  processing.Order  (Nexus)
apps.Order  ──►  fulfillment.Order  (Nexus)
```

During this migration, `processing/domain/v1/workflows.proto` retains `FulfillOrderRequest` and `FulfillOrderResponse` as internal messages — evidence of the old Kafka activity. These are internal to processing's workflow and do not cross into the fulfillment BC's proto package. They will be removed when the processing workflow is versioned to drop the old activity.

The rule: **a BC's proto package may reference its own internal messages freely, but it must never import from a sibling BC's proto package**. The cleanup of transitional messages happens at version cutover, not before.

**References:**
- Fowler, [Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html)
- Temporal, [Workflow Versioning](https://docs.temporal.io/workflow-versioning)

---

## Import Rules Summary

| Import | Allowed? | Reason |
|--------|----------|--------|
| `acme/common/v1/values.proto` | Yes, anywhere | Universal value types |
| `acme/oms/v1/*.proto` | Yes, from `apps` and domain services that handle OMS data | Shared OMS kernel |
| `acme/<bc>/domain/v1/*` from within the same BC | Yes | Self-reference |
| `acme/<bc>/domain/v1/*` from `apps` | Yes | Orchestrator depends on handler contracts |
| `acme/<bc>/domain/v1/*` from a sibling domain BC | **No** | Domain services must not couple to each other |
| `acme/apps/domain/v1/*` from any domain BC | **No** | Domain services must not couple to their orchestrator |

The last two rows are the ones that LLM-generated code tends to violate. When building a new handler that needs data originally sourced from another BC, the instinct is to reach for the type that already holds that data. Resist it: define the type you need in your own package and let the orchestrator perform the mapping.

---

## Checklist for Adding a New Operation

1. **Identify the handler.** Which BC executes the operation? That BC owns the contract.
2. **Name from the operation.** `doThing` → `DoThingRequest` / `DoThingResponse` in the handler's `workflows.proto`.
3. **Check import direction.** The handler's proto file must not import from any caller's proto package.
4. **Define data shapes locally.** If the request needs a nested data type, define it in the handler's `workflows.proto` or `values.proto`. Do not reuse a type from another BC's package even if the shape looks identical today.
5. **Map at the orchestrator.** If `apps` is passing data from one BC into another, write the explicit field-by-field mapping in `apps`'s workflow or service code. This is intentional; it is the ACL.
6. **Elevate to `common/v1` sparingly.** Only when the type is genuinely universal and appears independently across three or more BCs.
