# Workshop Specification

## Abstract
Beyond the Bot: Extending Production Applications with AI

Abstract:
This advanced, partner-exclusive workshop focuses on the architectural realities of evolving production Temporal applications. We will explore the specific capabilities within Temporal that simplify extending a stable system with agentic AI functionality, reducing the traditional burdens of cross-language orchestration and state management.

Using a production-grade Temporal application as our foundation, we’ll walk through how to review, extend, and safely introduce new AI-driven functionality without compromising the reliability of the core system. Across application, delivery, and integration workstreams, we will identify the “seams” in existing workflows where Temporal’s native features—such as polyglot support and durable execution—can be leveraged to incorporate specialized AI components and manage probabilistic reasoning.

Workshop Focus

Integration Seams
Identifying the most effective points within established workflows to introduce AI-driven optimization and fulfillment.

The Reliability Harness
Using Temporal’s durable execution model to wrap probabilistic AI tool-calling, preserving system integrity regardless of model variability.

Polyglot Capabilities
Leveraging Temporal’s cross-language support to bridge deterministic core logic with specialized agent runtimes.

(Future) Durable Human-in-the-Loop
Implementing long-lived, stateful intervention patterns that allow workflows to pause for expert validation while preserving process state over extended durations.





Why Attend


See how experienced teams use Temporal’s built-in capabilities to extend complex production systems.

Learn practical patterns for introducing AI functionality into existing customer environments without a “rip-and-replace” approach.

Equip your team to deliver real-world solutions that require a reliable bridge between deterministic business rules and probabilistic AI reasoning.

### Ideas

### Safe Extensibility

* Exercise 01 guide: [Safely Move Fulfillment Ownership](../../workshop/exercises/01-safe-fulfillment-handoff/README.md)

* Exercise 01 spec: [Safely Move Fulfillment Ownership](./exercises/01-safe-fulfillment-handoff/spec.md)

* Demo spec: [Temporal Worker Controller Rollout](./demos/temporal-worker-controller/spec.md)

* Python: Augmenting plain ShippingAPI with agent ReAct via Nexus

* Provide all the Temporal primitives (Nexus Ops, Activities, etc), just code the ReAct loop

* K8S: Ramp new traffic to the new fulfillment.Order with the Temporal Worker Controller

* Worker Versioning: Safely Route current traffic to Nexus fulfillment service handler instead of Kafka activity

### AI Decisioning

* Is this Agentic or non-Agentic?
* Probabilistic decision making in a hard-coded world
* Human-in-the-loop requirements with Temporal primitives
    * Async Activities
    * Nexus Operations
* Feeding back to the caller
* Deterministic parts shouldn't make the Reasoning parts expensive
* Code Your Tools to Interface with Temporal Primitives 
    * Extensible tool dispatch

### Visibility

* Temporal UI
    * See `margin_leak` or `sla_breach` (SearchAttribute) opportunities before "fixing it if ain't broke"
  
