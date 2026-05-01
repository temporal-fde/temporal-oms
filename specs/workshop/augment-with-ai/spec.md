# Workshop Specification: Augmenting Temporal Systems with AI

**Feature Name:** Augment with AI — Workshop Exercise Series
**Status:** Draft
**Owner:** Temporal FDE Team
**Created:** 2026-04-27
**Updated:** 2026-05-01

---

## Overview

### Executive Summary

This workshop teaches engineering teams how to safely introduce new AI-augmented behavior into a running Temporal system - specifically, how to route traffic from a legacy Kafka-based fulfillment path to a modern Nexus + AI-powered fulfillment path without disrupting in-flight orders.

The workshop runs entirely inside GitHub Codespaces using a local Temporal dev server (Level 1 — no Kubernetes, no cloud). Participants work through a series of exercises that build on each other: first learning to route traffic safely using Worker Deployments, then observing the AI system that traffic lands on, then extending it.

The system under study is this OMS repo itself. The arc is:

```
Exercise 01: Route traffic safely to new behavior (Worker Deployments + Nexus migration)
Exercise 02: Observe the AI in action (ShippingAgent reliability harness)
Exercise 03: Extend the AI (add a new capability to the ShippingAgent)
```

Exercise 01 is the primary safe rollout lab. Exercise 02 is a guided trace lab targeted at 55
minutes. Exercise 03 is the planned extension lab.

---

## Goals & Success Criteria

### Primary Goals

- Goal 1: Participants understand why Worker Deployment ramping is the correct mechanism for safe behavioral change (not application-level feature flags)
- Goal 2: Participants can describe the Nexus call graph from `apps.Order` → `fulfillment.Order` and what changed vs the Kafka path
- Goal 3: Participants understand UpdateWithStart as the pattern for AI workflow initialization
- Goal 4: Participants can add a new tool to an existing Temporal AI agent without breaking in-flight workflows

### Acceptance Criteria

- [ ] Codespaces environment starts and reaches ready state with a single script
- [ ] Exercise 01 completes end-to-end: Kafka drain observed, Nexus path verified
- [ ] Exercise 02 completes: participants can observe ShippingAgent workflow history, identify tool boundaries, and explain how `fulfillment.Order` applies the recommendation
- [ ] Exercise 03 completes: modified ShippingAgent runs with new tool, existing sessions unaffected
- [ ] Each exercise guide explains the "why" not just the "what"; exercises with code changes also
      include a SOLUTION.md

---

## Current State (As-Is)

### What exists today

- `GETTING_STARTED.md` describes a 5-terminal manual startup for local dev — not workshop-friendly
- The fulfillment handoff migration is moving to an explicit `send_fulfillment` routing slip in `ProcessOrderRequest.options`; the Exercise 01 lab now covers the coordinated `processing` and `apps` worker rollout
- ShippingAgent (Python, Claude-based) is implemented; Exercise 02 now has a planning spec, but no attendee-facing lab guide yet
- `scripts/scenarios/` has demo scripts, but Exercise 01 should use the sustained
  `WorkerVersionEnablement` traffic generator instead
- Root `workshop/exercises/` now contains Exercise 01 material; later exercises and the final
  single-command startup workflow still need to be implemented

### Gaps

- Codespaces/devcontainer setup is implemented; the attendee startup/reset workflow still needs to
  be finalized
- No final end-to-end startup/reset workflow for repeatable workshop runs
- No attendee-facing guided observation material for the ShippingAgent workflow pattern
- No scaffolded extension exercise for the AI agent

---

## Desired State (To-Be)

### Workshop Structure

```
workshop/
  README.md                               # Workshop arc, how exercises relate
  exercises/
    01-safe-fulfillment-handoff/
      README.md                           # Exercise narrative + guided questions (3 acts)
      SOLUTION.md                         # Step-by-step CLI + expected output + the "why"
    02-observe-shipping-agent/
      README.md
      scripts/
    03-extend-agent/                      # [TBD — see Open Questions]
      README.md
      SOLUTION.md
      starter/                            # Scaffolded starting point for extension

.devcontainer/
  devcontainer.json                       # Codespaces config — see Dependencies
```

### Related Foundation Exercise — Safely Move Fulfillment Ownership

The first workshop lab is not AI-specific. It establishes the safe-extensibility foundation that the
AI labs build on.

**The question this exercise answers:** "How do we move fulfillment orchestration from
`processing.Order` to `apps.Order` without disrupting in-flight orders or hiding rollout policy in
workflow code?"

The planning spec for this foundation exercise lives under `specs/`; the implemented lab lives
under the root `workshop/` directory:

- Spec: [`../exercises/01-safe-fulfillment-handoff/spec.md`](../exercises/01-safe-fulfillment-handoff/spec.md)
- Lab guide: [`../../../workshop/exercises/01-safe-fulfillment-handoff/README.md`](../../../workshop/exercises/01-safe-fulfillment-handoff/README.md)
- Solution: [`../../../workshop/exercises/01-safe-fulfillment-handoff/SOLUTION.md`](../../../workshop/exercises/01-safe-fulfillment-handoff/SOLUTION.md)

The chosen approach is a combination of:

- a routing slip in `ProcessOrderRequestExecutionOptions` (`send_fulfillment=false` from `apps v2`)
- manual Worker Deployment commands (`processing v2` first, then ramp `apps v2`), with TWC
  introduced later as the Kubernetes automation layer

The hands-on lab steps, scripts, and exact startup mechanics are intentionally deferred to the
top-level workshop exercise implementation plan. This section replaces the earlier
processing-only ramp proposal, which did not account for the coordinated ApplicationService →
DomainService ownership change.

### Exercise 02 - Observe The ShippingAgent Reliability Harness

The second lab is a guided trace exercise, not another rollout or coding lab.

Planning spec:

- [`../exercises/02-observe-shipping-agent/spec.md`](../exercises/02-observe-shipping-agent/spec.md)

Exercise 02 starts after Exercise 01 has routed new orders through `fulfillment.Order`. Participants
run or inspect one assigned order scenario, find the long-running `ShippingAgent` workflow by
`CUSTOMER_ID`, and trace the AI-assisted decision through Temporal history.

Key patterns:

- discovery-first rollout: use `margin_leak` and `sla_breach_days` Search Attributes to list the
  exact orders that need analysis before adding new process enforcement
- UpdateWithStart for per-customer agent workflow initialization
- LLM calls as Activities, not workflow code
- tool dispatch through Activities and Nexus operations
- workflow-layer hard guards around negative outcomes such as `MARGIN_SPIKE` and `SLA_BREACH`
- `ShippingAgent` recommends while `fulfillment.Order` applies the business decision and records
  Search Attributes
- follow-up design: if margin leakage later requires human approval, that long-running wait must be
  modeled explicitly instead of hidden behind the current synchronous 120-second `ShippingAgent`
  Nexus call

The target timebox is 55 minutes. The lab should control duplicate live LLM runs so rate limits do
not dominate the exercise.

### Exercise 03

**TBD - see Open Questions.** The intent is to give participants a scaffolded starting point and
ask them to add a new tool to the agent, for example a simulated carrier SLA lookup, without
breaking in-flight ShippingAgent sessions.

---

## Technical Approach

### Design Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Exercises are narrative-first, scripts second | The "why" must land before the "how"; scripts support, not replace, understanding | Script-first walk-throughs — participants follow steps without internalizing the concept |
| SOLUTION.md is a separate file when an exercise has code changes | Keeps exercise friction intentional; participants must choose to look | Hints directory with progressive reveals — adds file complexity for marginal benefit |
| Ramp via Temporal CLI (not TWC CRD) in Codespaces | Codespaces runs Level 1 (no k8s); CLI is the direct API the CRD wraps | Docker Compose with k8s-in-docker — over-engineering for a workshop that doesn't need production infra |
| exercise scripts use known fixed ports | Ports are stable in the devcontainer (8080, 8071, 8233); no service discovery needed | Port discovery via env vars — adds indirection for no benefit in this context |

### Devcontainer Requirements

See [Dependencies](#dependencies) for full detail. The exercises assume:
- Temporal dev server reachable at `localhost:7233`
- Apps API at `localhost:8080`
- Kafka admin at `localhost:8071`
- Temporal UI at `localhost:8233`
- `temporal` CLI available on PATH
- `jq` and `curl` available on PATH
- Baseline Java workers already running; Maven dependencies warm enough for the v2 rebuild steps

---

## Implementation Strategy

### Phase 1: Codespaces/devcontainer foundation

Deliverables:
- [x] `.devcontainer/devcontainer.json` - host requirements, features, port forwards, environment
- [x] `.devcontainer/Dockerfile` - pinned Temporal CLI, uv, buf, xh, kind, k3d, and k9s
- [x] `.devcontainer/on-create.sh` - Maven prebuild, Python dependency sync, and `.env.local` seed
- [x] `.devcontainer/k9s/` - instructor/developer k9s defaults

Completed on April 30, 2026.

### Phase 1b: Workshop startup runner

Deliverables:
- [ ] `scripts/workshop-start.sh` - starts Temporal dev server, runs `setup-temporal-namespaces.sh`, and starts local services
- [ ] `scripts/workshop-status.sh` - reports service, namespace, and Worker Deployment state
- [ ] `scripts/workshop-stop.sh` - stops services started by the workshop runner
- [ ] Verify clean Codespaces startup reaches ready state within the target timebox

### Phase 2: Exercise 01

Deliverables:
- [x] `workshop/README.md`
- [x] `workshop/exercises/01-safe-fulfillment-handoff/README.md`
- [x] `workshop/exercises/01-safe-fulfillment-handoff/SOLUTION.md`
- [ ] Optional helper: generated-order inspection script, if Temporal UI proof is too slow live

### Phase 3: Exercise 02

Deliverables:
- [x] `specs/workshop/exercises/02-observe-shipping-agent/spec.md`
- [x] `workshop/exercises/02-observe-shipping-agent/README.md`
- [x] Exercise helper scripts for status checks and scenario launch
- [ ] Optional deterministic LLM fallback or pre-recorded history fallback

### Phase 4: Exercise 03

Deliverables: TBD pending design decisions in Open Questions.

### Critical Files

To Create:
- `scripts/workshop-start.sh`
- `scripts/workshop-status.sh`
- `scripts/workshop-stop.sh`
- Optional generated-order inspection helper for Exercise 01

To Modify:
- `specs/README.md` — add workshop spec entry

---

## Testing Strategy

### Exercise 01 Validation

- [ ] `WorkerVersionEnablement` keeps submitting orders while `processing` and `apps` deployments change
- [ ] Generated orders can be inspected to identify v1 vs v2 path from Temporal UI and the Kafka admin endpoint
- [ ] CLI ramp commands succeed on local Temporal dev server (requires Temporal server >= 1.25 for Worker Deployments API)
- [ ] Both paths result in a `Completed` `fulfillment.Order` workflow
- [ ] Kafka admin endpoint at 8071 is accessible in Codespaces (port forwarded)

### Exercise 02 Validation

- [ ] Valid-order scenario reaches `ShippingAgent.recommendShippingOption`
- [ ] Margin-spike scenario shows `find_alternate_warehouse` before accepted `MARGIN_SPIKE`
- [ ] SLA-breach scenario shows `find_alternate_warehouse` before accepted `SLA_BREACH`
- [ ] `fulfillment.Order` exposes `margin_leak` or `sla_breach_days` for the relevant scenarios
- [ ] Participants can run Temporal UI visibility queries for `margin_leak` and `sla_breach_days`
- [ ] Exercise can run without exceeding LLM rate limits
- [ ] Fallback path exists if `ANTHROPIC_API_KEY` is missing or rate limited

### Full Workshop Dry Run

- [ ] Start from a fresh Codespaces instance
- [ ] Run `workshop-start.sh` to ready state
- [ ] Complete Exercise 01 end-to-end in < 45 minutes
- [ ] Complete Exercise 02 end-to-end in < 55 minutes
- [ ] Exercise commands work verbatim - no editing required

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| Temporal dev server version < 1.25 doesn't support Worker Deployments API | High — Exercise 01 Act 2 blocked | Medium | Pin Temporal CLI version in devcontainer; add version check to `workshop-start.sh` |
| Codespaces cold start too slow (Java build time) | Medium — workshop pacing killed | Medium | `onCreateCommand` pre-builds Maven and Python dependencies during container creation; participants work while it builds |
| Generated-order proof is slow to inspect manually | Low — pacing drag | Medium | Add a read-only inspection helper if needed; do not replace the enablements load generator |
| Python worker fails to start (missing API key) | Medium — Exercise 02/03 blocked | Medium | `workshop-start.sh` warns on missing keys but starts workers anyway; exercises that need real API keys are explicitly called out |
| LLM rate limits are hit during Exercise 02 | Medium — participants cannot complete live traces | Medium | Limit duplicate live runs and add deterministic or recorded fallback |
| In-flight v1 workflows don't complete before sunset step in Act 3 | Low — minor confusion | Low | The enablements generator uses fast generated orders; sunset delay is explicit in the exercise |

---

## Dependencies

### Codespaces/devcontainer

The devcontainer is implemented and includes:

- Base image: `mcr.microsoft.com/devcontainers/base:ubuntu-24.04`
- Host requirements: 4 cores, 16 GB RAM, 64 GB storage
- Features: Java 21 with Maven 3.9.9, Python 3.13, Node 25.2.1, Docker-in-Docker, kubectl/helm
- Pinned tools in the Dockerfile: Temporal CLI 1.7.0, uv 0.11.6, buf 1.46.0, xh 0.25.3, kind
  0.31.0, k3d 5.8.3, and k9s 0.50.18
- Forwarded ports: 7233, 8233, 8080, 8050, 8070, and 8071
- `onCreateCommand`: Maven prebuild, Python dependency sync, k9s config install, and `.env.local`
  seed from `.env.codespaces`

`workshop-start.sh` (run by participant after container is ready):
1. `temporal server start-dev --port 7233 --ui-port 8233 &`
2. Wait for Temporal ready (`temporal operator namespace list`)
3. `./scripts/setup-temporal-namespaces.sh`
4. Start all 5 worker processes in background (with log files)
5. Print ready message with port map

### External

- Temporal CLI >= 1.3.0 (Worker Deployment commands)
- Temporal Server >= 1.25 (Worker Deployments API)
- GitHub Codespaces with at least 4-core machine type (Java workers are memory-heavy)
- Anthropic API key for live Exercise 02 runs, unless deterministic fallback mode is implemented

---

## Open Questions

### For Tech Lead / Product

- [ ] What is the full exercise list? Is the arc (migration -> observe AI -> extend AI) the right one, or are there other exercises planned?
- [ ] Does Exercise 03 ask participants to write new Python code, or is it a configuration/integration exercise?
- [ ] Should `workshop-start.sh` start the Python worker automatically, or is starting the Python worker part of an exercise?
- [ ] Are Anthropic and OpenAI API keys expected to be pre-configured in the Codespaces environment (repo secrets), or do participants bring their own? EasyPost is only needed for offline fixture capture, not normal workshop runtime.
- [ ] Is the Kafka admin endpoint (port 8071) currently available when running with all workers, or does it only appear in a specific startup mode?
- [ ] Should Exercise 02 require a live LLM call, or should it default to a deterministic recorded-response mode with live LLM as an instructor option?
- [ ] Should the read-only `ShippingAgent.get_options` Query be implemented before Exercise 02 so participants can inspect cache state directly?

### Implementation Notes

- Exercise 01 should not call `scripts/scenarios/*`; `WorkerVersionEnablement` is the traffic source
  and keeps pumping orders through during the rollout.
- Exercise 02 should call `scripts/scenarios/*`; it needs deterministic, single-order AI
  scenarios rather than sustained load.
- The Codespaces machine type is specified in `devcontainer.json` - 4-core minimum to run Temporal + 5 JVM processes + Python worker without OOM
- `setup-temporal-namespaces.sh` already handles `set-current-version` for build-id `local` — `workshop-start.sh` must call this after starting workers, not before
- Exercise 01 Act 2 requires Temporal Server to support `set-ramping-version` — verify this command exists in the pinned CLI version before Phase 2 begins

---

## References

- `java/processing/processing-core/src/main/java/com/acme/processing/workflows/OrderImpl.java` — version gate
- `java/processing/processing-core/src/main/java/com/acme/processing/workflows/activities/FulfillmentsImpl.java` — Kafka activity
- `java/fulfillment/fulfillment-core/src/main/java/com/acme/fulfillment/services/FulfillmentImpl.java` — Nexus handler
- `python/fulfillment/src/agents/workflows/shipping_agent.py` — ShippingAgent workflow
- `python/fulfillment/src/services/shipping_agent_impl.py` — ShippingAgent Nexus handler and UpdateWithStart bridge
- `scripts/scenarios/README.md` — valid, margin-spike, and SLA-breach scenarios for Exercise 02
- `k8s/processing-versioned/base/temporal-worker-deployment.yaml` — production TWC equivalent
- `scripts/setup-temporal-namespaces.sh` — namespace + version setup (called by workshop-start.sh)
- `GETTING_STARTED.md` — Level 1 manual startup (what devcontainer automates)
