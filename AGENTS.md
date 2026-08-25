# AGENTS.md

This repository contains the ACME Order Management System reference app, a
multi-namespace Temporal workshop application with Java workers, Python
fulfillment and agent workflows, generated protobuf contracts, Kubernetes
deployment assets, and a Svelte web UI.

## Agent Behavior Rules

Cross-cutting behavior rules live under `.claude/rules/`, indexed at
`.claude/rules/README.md`. The rules govern how an agent works in the
repository, while this file governs repo-specific orientation and engineering
constraints.

Before doing repository work, skim `.claude/rules/README.md` and open any rule
that applies to the task. For this checkout, the repo-local `.claude/rules/`
copy is the source to cite and keep in sync.

## Required Temporal Skills

This is a Temporal repository. Before touching Temporal workflow, activity,
worker, Nexus, namespace, Worker Versioning, deployment, operational, testing,
or documentation concerns, load a Temporal skill.

Preferred routing:

- Use `temporal-developer` or `skill-temporal-developer` for Temporal SDK code,
  workflow and activity design, replay safety, worker implementation, testing,
  and Temporal application documentation.
- If that skill is unavailable, use the most specific Temporal skill available:
  `stack-temporal` for general Temporal application work,
  `stack-temporal-python` for Python SDK work, `temporal-ops` for Temporal
  Cloud, server, CLI, namespace, task queue, and workflow diagnosis, and
  `deployment-kubernetes-local` for local Kubernetes or Temporal Worker
  Controller work.
- Pair the Temporal skill with language or layer skills when relevant:
  `stack-java`, `stack-python`, `stack-typescript`, `stack-frontend`,
  `schema-protobuf`, or similar.

If no Temporal skill can be loaded, say that explicitly and continue from the
repository docs, specs, code, tests, and official Temporal documentation when
current product behavior or API details are uncertain.

## Repository Orientation

Before making changes:

1. Inspect `git status` so existing user changes are visible.
2. Read `README.md` for the app model and current workshop shape.
3. Read `specs/README.md` and any relevant feature spec under `specs/`.
4. Read the relevant local guide: `docs/GETTING_STARTED.md`,
   `docs/DEVELOPMENT.md`, `docs/DEPLOYMENT.md`, or the matching workshop docs.
5. Inspect nearby tests and generated-code boundaries before editing code.

## Temporal Engineering Constraints

- Preserve workflow determinism. Do not add wall-clock time, random values,
  network calls, filesystem access, environment reads, mutable globals, or
  other non-deterministic behavior inside workflow code.
- Put I/O, service calls, LLM calls, filesystem access, randomness, and
  secret-bearing operations in Activities or other appropriate Temporal
  primitives, not directly in Workflows.
- Treat workflow history as durable data. Do not put secrets, API keys, access
  tokens, or unnecessary PII in workflow inputs, signals, updates, search
  attributes, logs, or exceptions.
- Maintain bounded-context separation. The app uses `apps`, `processing`, and
  fulfillment boundaries; cross-boundary calls should preserve the existing
  Temporal namespace and Nexus model unless a spec changes it.
- Worker Versioning and Temporal Deployments are part of the product surface.
  When changing worker behavior, consider replay compatibility, pinned
  workflows, drain behavior, build IDs, and rollout scripts.
- Add or update replay tests for workflow behavior changes. A single workflow
  type still needs replay coverage when its logic changes.
- For protobuf changes, update the source `.proto` files first, then regenerate
  Java, Python, and web outputs with the repo's buf workflow.
- Keep Temporal Cloud and local Temporal behavior distinct in docs and scripts.
  Do not assume one environment when the current context is ambiguous.

## Validation

Run the narrowest checks that cover the change, and broaden when the change
crosses module or runtime boundaries.

Common checks:

```bash
mvn -f /Users/mnichols/dev/fde-temporal-oms/java/pom.xml test
uv run --project /Users/mnichols/dev/fde-temporal-oms/python pytest
npm --prefix /Users/mnichols/dev/fde-temporal-oms/web run check
npm --prefix /Users/mnichols/dev/fde-temporal-oms/web run lint
buf lint /Users/mnichols/dev/fde-temporal-oms/proto
```

For workshop or deployment changes, also validate the relevant script path under
`scripts/`, `k8s/`, or `workshop/`, and report any environment prerequisites
that prevented a full run.
