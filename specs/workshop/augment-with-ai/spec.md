# Workshop Specification: Augmenting Temporal Systems with AI

**Feature Name:** Augment with AI — Workshop Exercise Series
**Status:** Draft
**Owner:** Temporal FDE Team
**Created:** 2026-04-27
**Updated:** 2026-04-27

---

## Overview

### Executive Summary

This workshop teaches engineering teams how to safely introduce new AI-augmented behavior into a running Temporal system — specifically, how to route traffic from a legacy Kafka-based fulfillment path to a modern Nexus + AI-powered fulfillment path without disrupting in-flight orders.

The workshop runs entirely inside GitHub Codespaces using a local Temporal dev server (Level 1 — no Kubernetes, no cloud). Participants work through a series of exercises that build on each other: first learning to route traffic safely using Worker Deployments, then observing the AI system that traffic lands on, then extending it.

The system under study is this OMS repo itself. The arc is:

```
Exercise 01: Route traffic safely to new behavior (Worker Deployments + Nexus migration)
Exercise 02: Observe the AI in action (ShippingAgent — Temporal AI workflow pattern)
Exercise 03: Extend the AI (add a new capability to the ShippingAgent)
```

Each exercise is ~20-30 minutes. The full workshop is designed to run in a 2-3 hour session.

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
- [ ] Exercise 02 completes: participants can observe ShippingAgent workflow history and query its state
- [ ] Exercise 03 completes: modified ShippingAgent runs with new tool, existing sessions unaffected
- [ ] Each exercise has a SOLUTION.md that explains the "why" not just the "what"

---

## Current State (As-Is)

### What exists today

- `GETTING_STARTED.md` describes a 5-terminal manual startup for local dev — not workshop-friendly
- The fulfillment handoff migration is moving to an explicit `send_fulfillment` routing slip in `ProcessOrderRequest.options`; there is no guided exercise yet showing how to deploy the coordinated `processing` and `apps` worker versions
- ShippingAgent (Python, Claude-based) is implemented but no exercise material exists
- `scripts/scenarios/` has demo scripts, but Exercise 01 should use the sustained
  `WorkerVersionEnablement` traffic generator instead
- Root `workshop/exercises/` now contains Exercise 01 material; later exercises and the final
  devcontainer workflow still need to be implemented

### Gaps

- No Codespaces/devcontainer setup — participants must manually configure 5 services
- No narrative connecting the migration gate to the Worker Deployment API
- No guided observation of the ShippingAgent workflow pattern
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
    02-shipping-agent/                    # [TBD — see Open Questions]
      README.md
      SOLUTION.md
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

### Exercises 02 and 03

**TBD — see Open Questions.** The intent:

- Exercise 02 focuses on observing `ShippingAgent` (`python/fulfillment/src/agents/`) running as a Temporal workflow. Key patterns: UpdateWithStart for per-customer session initialization, the LLM ReAct loop as a Temporal workflow, tool dispatch as Activities.
- Exercise 03 gives participants a scaffolded starting point and asks them to add a new tool to the agent (e.g., a simulated "carrier SLA lookup") without breaking in-flight ShippingAgent sessions.

---

## Technical Approach

### Design Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Exercises are narrative-first, scripts second | The "why" must land before the "how"; scripts support, not replace, understanding | Script-first walk-throughs — participants follow steps without internalizing the concept |
| SOLUTION.md is a separate file, not hints | Keeps exercise friction intentional; participants must choose to look | Hints directory with progressive reveals — adds file complexity for marginal benefit |
| Ramp via Temporal CLI (not TWC CRD) in Codespaces | Codespaces runs Level 1 (no k8s); CLI is the direct API the CRD wraps | Docker Compose with k8s-in-docker — over-engineering for a workshop that doesn't need production infra |
| exercise scripts use known fixed ports | Ports are stable in the devcontainer (8080, 8071, 8233); no service discovery needed | Port discovery via env vars — adds indirection for no benefit in this context |

### Devcontainer Requirements (hard dependency for exercises)

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

### Phase 1: Devcontainer (blocking dependency)

Deliverables:
- [x] `.devcontainer/devcontainer.json` — base image, features (Java 21, Python 3.13, Temporal CLI), port forwards
- [ ] `scripts/workshop-start.sh` — starts Temporal dev server + runs `setup-temporal-namespaces.sh` + starts all 5 worker processes
- [ ] Verify clean Codespaces cold start takes < 5 min to ready state

### Phase 2: Exercise 01

Deliverables:
- [x] `workshop/README.md`
- [x] `workshop/exercises/01-safe-fulfillment-handoff/README.md`
- [x] `workshop/exercises/01-safe-fulfillment-handoff/SOLUTION.md`
- [ ] Optional helper: generated-order inspection script, if Temporal UI proof is too slow live

### Phase 3: Exercises 02 and 03

Deliverables: TBD pending design decisions in Open Questions.

### Critical Files

To Create:
- `.devcontainer/devcontainer.json`
- `scripts/workshop-start.sh`
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

### Full Workshop Dry Run

- [ ] Start from a fresh Codespaces instance
- [ ] Run `workshop-start.sh` to ready state
- [ ] Complete Exercise 01 end-to-end in < 30 minutes
- [ ] SOLUTION.md commands work verbatim — no editing required

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| Temporal dev server version < 1.25 doesn't support Worker Deployments API | High — Exercise 01 Act 2 blocked | Medium | Pin Temporal CLI version in devcontainer; add version check to `workshop-start.sh` |
| Codespaces cold start too slow (Java build time) | Medium — workshop pacing killed | Medium | `postCreateCommand` pre-builds during container creation; participants work while it builds |
| Generated-order proof is slow to inspect manually | Low — pacing drag | Medium | Add a read-only inspection helper if needed; do not replace the enablements load generator |
| Python worker fails to start (missing API key) | Medium — Exercise 02/03 blocked | Medium | `workshop-start.sh` warns on missing keys but starts workers anyway; exercises that need real API keys are explicitly called out |
| In-flight v1 workflows don't complete before sunset step in Act 3 | Low — minor confusion | Low | The enablements generator uses fast generated orders; sunset delay is explicit in the exercise |

---

## Dependencies

### Devcontainer (Phase 1 blocker)

Minimum devcontainer config:
- Base image: `mcr.microsoft.com/devcontainers/java:21`
- Features: Python 3.11, Temporal CLI (pinned version), `uv`, `jq`
- Ports: 8080, 8071, 8233, 7233
- `postCreateCommand`: `cd java && mvn clean install -DskipTests && cd ../python/fulfillment && uv sync`

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

---

## Open Questions

### For Tech Lead / Product

- [ ] What is the full exercise list? Is the arc (migration → observe AI → extend AI) the right one, or are there other exercises planned?
- [ ] Does Exercise 03 ask participants to write new Python code, or is it a configuration/integration exercise?
- [ ] Should `workshop-start.sh` start the Python worker automatically, or is starting the Python worker part of an exercise?
- [ ] Are Anthropic and OpenAI API keys expected to be pre-configured in the Codespaces environment (repo secrets), or do participants bring their own? EasyPost is only needed for offline fixture capture, not normal workshop runtime.
- [ ] Is the Kafka admin endpoint (port 8071) currently available when running with all workers, or does it only appear in a specific startup mode?

### Implementation Notes

- Exercise 01 should not call `scripts/scenarios/*`; `WorkerVersionEnablement` is the traffic source
  and keeps pumping orders through during the rollout.
- The Codespaces machine type needs to be specified in `devcontainer.json` — 4-core minimum to run Temporal + 5 JVM processes + Python worker without OOM
- `setup-temporal-namespaces.sh` already handles `set-current-version` for build-id `local` — `workshop-start.sh` must call this after starting workers, not before
- Exercise 01 Act 2 requires Temporal Server to support `set-ramping-version` — verify this command exists in the pinned CLI version before Phase 2 begins

---

## References

- `java/processing/processing-core/src/main/java/com/acme/processing/workflows/OrderImpl.java` — version gate
- `java/processing/processing-core/src/main/java/com/acme/processing/workflows/activities/FulfillmentsImpl.java` — Kafka activity
- `java/fulfillment/fulfillment-core/src/main/java/com/acme/fulfillment/services/FulfillmentImpl.java` — Nexus handler
- `k8s/processing-versioned/base/temporal-worker-deployment.yaml` — production TWC equivalent
- `scripts/setup-temporal-namespaces.sh` — namespace + version setup (called by workshop-start.sh)
- `GETTING_STARTED.md` — Level 1 manual startup (what devcontainer automates)
