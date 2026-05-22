# Workshop Diagrams

**Status:** Draft visual narrative pack
**Owner:** Temporal FDE Team
**Purpose:** Maintain workshop-ready visuals for the Kafka fulfillment to `fulfillment.Order` and
`ShippingAgent` architecture story.

This directory is separate from `/specs` on purpose. Specs remain the design and planning material;
this directory holds visual artifacts used for workshop slides, whiteboards, exports, and iteration.

## Directory Layout

```text
diagrams/workshop/
├── README.md
├── briefs/        # diagram intent, speaker notes, and source references
├── mermaid/       # canonical importable Mermaid source
├── exports/       # generated PNG/SVG/PDF assets for slides
└── excalidraw/    # optional hand-polished Excalidraw versions
```

## Visual Sequence

| # | Brief | Mermaid Source | Job in the Workshop |
|---|---|---|---|
| 01 | [Current Kafka Fulfillment Path](./briefs/01-current-kafka-path.md) | [`.mmd`](./mermaid/01-current-kafka-path.mmd) | Establish the V1 baseline and its operational limits |
| 02 | [Motivation Gap Map](./briefs/02-motivation-gap-map.md) | [`.mmd`](./mermaid/02-motivation-gap-map.mmd) | Connect pains to architectural needs before showing the solution |
| 03 | [Safe Fulfillment Handoff Rollout](./briefs/03-safe-fulfillment-handoff-rollout.md) | [`.mmd`](./mermaid/03-safe-fulfillment-handoff-rollout.mmd) | Explain how Worker Versioning and the routing slip prevent disruption |
| 04 | [Final Fulfillment Order Architecture](./briefs/04-final-fulfillment-order-architecture.md) | [`.mmd`](./mermaid/04-final-fulfillment-order-architecture.mmd) | Show the desired durable orchestration boundary |
| 05 | [ShippingAgent Loop](./briefs/05-shipping-agent-loop.md) | [`.mmd`](./mermaid/05-shipping-agent-loop.mmd) | Show where agentic workflows enter without taking over business ownership |
| 06 | [Proof and Observability](./briefs/06-proof-and-observability.md) | [`.mmd`](./mermaid/06-proof-and-observability.mmd) | Give participants concrete signals to verify the migration worked |

## Source Specs

- [`fulfillment.Order` workflow spec](../../specs/fulfillment-order/fulfillment-order-workflow/spec.md)
- [`ShippingAgent` spec](../../specs/fulfillment-order/shipping-agent/spec.md)
- [Exercise 01 safe handoff spec](../../specs/workshop/exercises/01-safe-fulfillment-handoff/spec.md)
- [Workshop spec](../../specs/workshop/spec.md)

## Working Rules

- Keep the `.mmd` files as the canonical diagram-as-code source.
- Keep speaker intent and workshop notes in `briefs/`.
- Generated slide assets go in `exports/`; hand-polished Excalidraw versions go in `excalidraw/`.
- Use the repo terms exactly: `apps.Order`, `processing.Order`, `fulfillment.Order`, `ShippingAgent`, Nexus, Worker Versioning.
- Make the reliability story land before the AI story. The AI agent is only compelling once the durable orchestration boundary is clear.
- Keep rollout policy separate from business behavior: Worker Versioning routes code; the routing slip records the per-order contract.

## Suggested Tool Flow

1. Edit Mermaid in `mermaid/*.mmd`.
2. Paste into Mermaid Chart, Lucid, MermanDraw, or an Excalidraw Mermaid converter.
3. Export slide-ready assets into `exports/`.
4. If a diagram needs a workshop-whiteboard feel, polish it in Excalidraw and store the `.excalidraw` file in `excalidraw/`.

## Suggested Slide Language

- Gray: legacy Kafka path
- Blue: Temporal workflows
- Green: Nexus operations and Updates
- Purple: ShippingAgent / LLM reasoning
- Orange: risk, margin, SLA, and operational gaps

## Narrative Spine

The workshop should not frame this as "we added AI to fulfillment." The stronger frame is:

> We moved fulfillment into a durable orchestration boundary, then attached a specialized agent
> where probabilistic shipping reasoning is useful, while keeping deterministic business decisions
> in `fulfillment.Order`.

