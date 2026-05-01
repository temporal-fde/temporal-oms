# Workshop Exercises

This directory contains the implemented, attendee-facing workshop exercises.

Specs remain under `specs/workshop/` and describe the intent, constraints, and design decisions.
Exercise directories here are the runnable lab material: what to do, what to observe, where to look
when validating behavior, and any exercise-specific `scripts/` needed to run the lab.

## Initial Setup

Before starting the exercises:

1. Create `.env.local` if it does not already exist:

   ```sh
   cp -n .env.codespaces .env.local
   ```

2. Follow the link your instructor gives you to get the command that updates `.env.local` with
   `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`. Alternatively, add your own values for those keys to
   `.env.local`.

## Exercises

| Exercise | Guide | Solution | Source Spec |
|---|---|---|---|
| 01: Safely Move Fulfillment Ownership | [README.md](exercises/01-safe-fulfillment-handoff/README.md) | [SOLUTION.md](exercises/01-safe-fulfillment-handoff/SOLUTION.md) | [spec.md](../specs/workshop/exercises/01-safe-fulfillment-handoff/spec.md) |
| 02: Observe The ShippingAgent Reliability Harness | [README.md](exercises/02-observe-shipping-agent/README.md) | N/A | [spec.md](../specs/workshop/exercises/02-observe-shipping-agent/spec.md) |
