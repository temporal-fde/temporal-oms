# Workshops

> WELCOME!

This directory contains the implemented, attendee-facing workshops.

Specs remain under `specs/workshop/` and describe the intent, constraints, and design decisions.
Workshop directories here are the runnable lab material: what to do, what to observe, where to look
when validating behavior, and any workshop-specific `scripts/` needed to run the lab.

## Initial Setup

Before starting a workshop:

1. Create `.env.local` if it does not already exist:

   ```sh
   cp -n .env.codespaces .env.local
   ```

2. Follow the link your instructor gives you to get the command that updates `.env.local` with
   `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`. Alternatively, add your own values for those keys to
   `.env.local`.

## Workshops

| Workshop | Guide | Solution | Source Spec |
|---|---|---|---|
| Safely Move Fulfillment Ownership | [README.md](safe-fulfillment-handoff/README.md) | [SOLUTION.md](safe-fulfillment-handoff/SOLUTION.md) | [spec.md](../specs/workshop/safe-fulfillment-handoff/spec.md) |
| Observe The ShippingAgent Reliability Harness | [README.md](observe-shipping-agent/README.md) | N/A | [spec.md](../specs/workshop/observe-shipping-agent/spec.md) |
