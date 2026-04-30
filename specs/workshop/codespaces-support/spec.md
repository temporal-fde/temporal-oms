# Codespaces Support Planning Spec

**Workshop:** Replay 2026 Temporal OMS workshop
**Status:** Planning
**Updated:** 2026-04-30

## Overview

This spec plans the GitHub Codespaces runtime for the Replay 2026 Temporal OMS workshop.
The primary decision is to keep attendee hands-on exercises out of Kubernetes and run the
OMS as plain local processes inside a devcontainer. Kubernetes remains relevant for the later
Temporal Worker Controller demo, but that demo should be instructor-controlled until the k8s path is
validated in Codespaces. A local k3d spike has validated the basic Kubernetes feasibility on a
developer machine; Codespaces validation is still pending.

For the concrete remote k3d validation procedure, use
[`k3d-remote-runbook.md`](./k3d-remote-runbook.md). The runbook is intentionally scoped to
instructor/maintainer validation and should not be treated as attendee workshop setup.

External facts checked while preparing this spec:

- GitHub Codespaces supports setting minimum machine requirements with `hostRequirements` in
  `devcontainer.json`, and under-resourced machine types can be filtered out for the repo:
  [GitHub Docs, minimum machine specification](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/configuring-dev-containers/setting-a-minimum-specification-for-codespace-machines).
- GitHub's Codespaces machines API examples include 4 core / 16 GB RAM and 8 core / 32 GB RAM
  Linux machine types:
  [GitHub Docs, Codespaces machines API](https://docs.github.com/en/rest/codespaces/machines).
- Codespaces prebuilds are designed to reduce setup time for large or complex repositories, and
  prebuilds run `onCreateCommand` and `updateContentCommand`, not `postCreateCommand`:
  [GitHub Docs, Codespaces prebuilds](https://docs.github.com/en/codespaces/prebuilding-your-codespaces/about-github-codespaces-prebuilds).
- Codespaces secrets are exported as runtime environment variables and are not available during
  Dockerfile or feature build time:
  [GitHub Docs, Codespaces secrets](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-your-account-specific-secrets-for-github-codespaces).
- Codespaces can forward and label ports from the codespace:
  [GitHub Docs, port forwarding](https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace).
- k3d runs k3s clusters in Docker, requires Docker and kubectl, and is positioned for local
  Kubernetes development:
  [k3d docs](https://k3d.io/stable/).
- K3s is a lightweight Kubernetes distribution with a single binary/minimal image and sqlite as the
  default datastore:
  [K3s docs](https://docs.k3s.io/).
- KinD runs each Kubernetes node as a Docker container and uses kubeadm to initialize the node:
  [KinD design docs](https://kind.sigs.k8s.io/docs/design/initial/).
- k3d supports importing local Docker images and managed registries:
  [k3d image import](https://k3d.io/stable/usage/commands/k3d_image_import/),
  [k3d registries](https://k3d.io/stable/usage/registries/).
- Temporal Worker Controller automates Worker Versioning on Kubernetes and is still the right
  production demo concept:
  [Temporal Worker Controller README](https://github.com/temporalio/temporal-worker-controller).

## Goals

- Provide a Codespaces plan that can support 40-50 attendees for a 3.5 hour workshop.
- Keep Exercise 01 within a 45 minute timebox.
- Make Exercise 01 reliable without Kubernetes, Docker image builds, manual file copying, or
  attendee-specific rebuild debugging.
- Preserve the intended learning objective: manual Temporal Worker Deployment commands first,
  Temporal Worker Controller automation later.
- Define runtime topology, ports, machine sizing, dependency caching, secrets handling, readiness
  checks, risks, and blockers before exercise script implementation starts.

## Non-goals

- Do not implement the full devcontainer, process supervisor, or Exercise 01 scripts in this phase.
- Do not replace or remove KinD support. k3d support is a parallel path.
- Do not require TWC, Kubernetes, Temporal Cloud, Docker Compose, EasyPost, or PredictHQ for
  Exercise 01.
- Do not make attendee setup depend on building Docker images during the workshop.
- Do not hide Exercise 01 rollout behavior behind application-level runtime feature flags.

## Current Runtime Requirements

Temporal dev server:

- Temporal gRPC: `127.0.0.1:7233`
- Temporal UI: `127.0.0.1:8233`
- Temporal namespaces:
  - `apps`
  - `processing`
  - `fulfillment`
  - `default` or `enablements` for enablement workers, currently defaulted to `default`

Nexus endpoints created by `scripts/setup-temporal-namespaces.sh`:

- `oms-processing-v1` -> `processing` namespace, `processing` task queue
- `oms-apps-v1` -> `apps` namespace, `apps` task queue
- `oms-integrations-v1` -> `default` or enablements namespace, `integrations` task queue
- `oms-fulfillment-v1` -> `fulfillment` namespace, `fulfillment` task queue
- `oms-fulfillment-agents-v1` -> `fulfillment` namespace, `agents` task queue

Fulfillment search attributes created by `scripts/setup-temporal-namespaces.sh`:

- `margin_leak` as `Int`
- `sla_breach_days` as `Int`

Local processes likely needed for attendee exercises:

| Process | Purpose | Port or task queues |
|---|---|---|
| Temporal dev server | Temporal runtime and UI | `7233`, `8233` |
| `apps-api` | Order submission and payment API | `8080`, management `9091` |
| `enablements-api` | Fixture-backed commerce, inventory, shipping, and location integrations; must not start Temporal pollers | `8050`, management `9050` |
| `apps-workers` | `apps.Order` workflows | `apps` task queue |
| `processing-workers` | `processing.Order`, support workflow, legacy Kafka proof endpoint | `processing`, `commerce-app`, `support`; app port `8071`, management `9082` |
| `fulfillment-workers` | Java `fulfillment.Order` workflow and fulfillment Nexus service | `fulfillment`, `fulfillment-carriers`; management `9072` |
| `enablements-workers` | Enablement workflows and integration Nexus handlers | `enablements`, `integrations`; management `9072` if not moved |
| Python fulfillment worker | ShippingAgent and shipping activities | `agents`, `fulfillment-shipping` |

Current repo observations that affect planning:

- `java/apps/apps-core/src/main/resources/acme.apps.yaml` and
  `java/processing/processing-core/src/main/resources/acme.processing.yaml` already enable Worker
  Versioning with deployment names from `TEMPORAL_DEPLOYMENT_NAME` and build IDs from
  `TEMPORAL_WORKER_BUILD_ID`.
- `proto/acme/processing/domain/v1/workflows.proto` does not yet include
  `optional bool send_fulfillment = 3`.
- `java/processing/processing-core/src/main/java/com/acme/processing/workflows/OrderImpl.java`
  currently uses `Workflow.getVersion("remove-kafka-fulfillment", ...)` to skip the Kafka handoff,
  rather than the planned routing-slip option.
- `java/apps/apps-core/src/main/java/com/acme/apps/workflows/OrderImpl.java` already starts
  `fulfillment.Order` and calls processing, but it does not set `send_fulfillment=false` because the
  field does not exist yet.
- The local Kafka proof is the embedded Kafka consumer in `processing-workers`, exposed through
  `GET /admin/order-fulfillment/{orderId}` on the processing worker local app port `8071`.
- `enablements-api` is API-like, not worker-like. It sets `spring.temporal.start-workers=false`.
  Temporal Spring may still construct/register configured worker objects when `spring.temporal.workers`
  is present, but it must not start polling. Readiness checks should distinguish registration logs
  from actual pollers.
- The current Kubernetes manifests include a `TemporalWorkerDeployment` path for processing only.
  The practical TWC path needs `TemporalWorkerDeployment` coverage for `apps`, `processing`, and
  `fulfillment`. The plain `processing-workers` Deployment can remain as reference material for
  comparison, but should not be the operational path for the workshop.
- A local k3d failure was caused by stale packaged Maven artifacts: source and `target/classes`
  no longer had a `@ConditionalOnProperty(name="spring.temporal.start-workers")` annotation on the
  enablements Nexus service beans, but the packaged `enablements-core` jar inside
  `enablements-api` still did. Rebuilding the Maven reactor slice and Docker image fixed
  `enablements-api` in k3d. This is exactly the kind of ad hoc rebuild debugging Exercise 01 must
  avoid.

## Options Considered

| Option | Fit for Exercise 01 | Pros | Cons | Recommendation |
|---|---|---|---|---|
| Plain local processes in Codespaces | High | Lowest runtime surface area; no Docker image build loop; direct Temporal CLI; easiest to explain Worker Deployment commands | Needs a reliable process supervisor and prebuilt v1/v2 artifacts | Use for attendee hands-on exercises |
| Docker Compose in Codespaces | Medium | One command can start services; isolates per-service env | Still requires Docker and image builds/pulls; no TWC benefit; extra networking/logging failure modes | Keep as fallback only if local supervision proves unreliable |
| KinD in Codespaces | Low for hands-on, medium for TWC | Existing scripts and manifests support KinD; good fallback and known local path | Heavier control plane; image load loop; not needed for Exercise 01 | Keep as supported instructor/demo path |
| k3d in Codespaces | Low for hands-on, promising for TWC | k3d runs lightweight k3s in Docker; K3s is designed for lighter environments; k3d has image import and managed registry support; local TWC validation passed | Codespaces Docker networking and resource behavior still need validation; apps and fulfillment TWD manifests still need to be added | Add as a parallel instructor/demo path, not the attendee Exercise 01 path |
| Hybrid | High | Local processes for exercises, instructor-controlled k8s for TWC | Requires two clearly separated runbooks | Recommended architecture |

## Recommended Architecture

Use a hybrid workshop architecture:

1. Attendee Codespaces run Exercise 01 and later AI exercises as plain local processes.
2. A devcontainer pins tools and prebuilds dependencies.
3. `scripts/workshop-start.sh` becomes the single attendee startup command.
4. Exercise 01 uses Temporal CLI Worker Deployment commands against the local Temporal dev server.
5. TWC/Kubernetes remains an instructor-led demo, run from a prevalidated local machine or a
   dedicated high-resource Codespace, not from every attendee Codespace.
6. k3d is the preferred Kubernetes candidate for the optional/instructor path if Codespaces
   validation confirms Docker-in-Codespaces networking and resources match the local spike.
7. Keep Kubernetes demo scripts split by runtime:
   - `scripts/kind/*` for KinD
   - `scripts/k3d/*` for k3d

This keeps Exercise 01 focused on Temporal primitives:

- `temporal worker deployment set-current-version`
- `temporal worker deployment set-ramping-version`
- pinned executions staying on their starting Worker Deployment Version
- the routing slip visible in workflow input/history

Kubernetes does not add value to the hands-on Exercise 01 path. It adds setup risk, resource
pressure, and a second orchestration model before attendees have learned the underlying Temporal
operations.

## Codespaces Machine/Devcontainer Requirements

Minimum attendee machine:

```json
{
  "hostRequirements": {
    "cpus": 4,
    "memory": "16gb",
    "storage": "64gb"
  }
}
```

Rationale:

- A 2 core / 8 GB machine is too tight for Temporal dev server, 5-6 JVM processes, the Python
  worker, Maven/uv cache, and VS Code.
- GitHub's current examples show 4 core / 16 GB and 8 core / 32 GB Linux machine classes in the
  Codespaces machines API.
- The Kubernetes manifests currently allow up to `1Gi` for APIs and `2Gi` for several worker pods;
  local JVMs need explicit memory caps so they do not collectively consume the 16 GB machine.

Recommended attendee devcontainer:

- Java 21 and Maven 3.9.x, matching `.tool-versions`.
- Python via `uv`; use the repo's `python/uv.lock`.
- Temporal CLI pinned to a version that supports Worker Deployment commands used by the lab.
- `jq`, `curl` or `xh`, `git`, `procps`, and shell utilities.
- No Docker requirement for the default attendee path.
- `forwardPorts` for `8233`, `8080`, `8050`, `8070`, and `8071`; optionally `7233` for CLI access
  from outside the codespace.
- `portsAttributes` labels so attendees can identify Temporal UI, Apps API, Enablements API,
  Processing API, and Kafka proof endpoint.

Recommended instructor or optional k8s machine:

- 8 cores / 32 GB RAM / 64 GB storage minimum.
- Docker, kubectl, helm, k9s, and either KinD or k3d.
- Prebuilt Docker images or a local registry before the live demo.

## Startup Model

`scripts/workshop-start.sh` should be a process supervisor, not a build script.

Recommended startup sequence:

1. Verify machine resources, tool versions, and free ports.
2. In Codespaces, create `.env.local` from `.env.codespaces` if missing. For non-Codespaces local
   development, `.env.example` remains the general template.
3. Start `temporal server start-dev` on `127.0.0.1:7233` with UI on `8233`.
4. Wait for Temporal frontend and default namespace readiness.
5. Run `scripts/setup-temporal-namespaces.sh`.
6. Start `enablements-api`.
7. Start baseline `apps-api`.
8. Start baseline v1 workers:
   - `apps-workers` with `TEMPORAL_DEPLOYMENT_NAME=apps` and `TEMPORAL_WORKER_BUILD_ID=v1`
   - `processing-workers` with `TEMPORAL_DEPLOYMENT_NAME=processing` and
     `TEMPORAL_WORKER_BUILD_ID=v1`
   - `fulfillment-workers`
   - `enablements-workers`
   - Python worker via `cd python/fulfillment && uv run --project .. python -m src.worker`
   - unique management ports for every JVM worker, or management disabled where it is not needed
9. Set current versions explicitly:
   - `apps` current -> `v1`
   - `processing` current -> `v1`
   - `fulfillment` current -> the chosen baseline build ID if fulfillment versioning is enabled.
10. Run readiness checks and print the exact URLs, log files, and next exercise command.

Recommended process layout:

- PID files: `.workshop/run/*.pid`
- Logs: `.workshop/logs/*.log`
- Status command: `scripts/workshop-status.sh`
- Stop command: `scripts/workshop-stop.sh`
- No Maven compile or Docker build during `workshop-start.sh`; those must happen in prebuild.

## Exercise 01 Requirements

Exercise 01 can and should avoid Kubernetes entirely.

Required runtime behavior:

- `processing v1` publishes the legacy Kafka fulfillment handoff.
- `processing v2` supports `send_fulfillment` and defaults an absent value to `true`.
- `apps v1` does not set `send_fulfillment`, so it remains compatible with `processing v2`.
- `apps v2` starts `fulfillment.Order` and sends `send_fulfillment=false` to `processing`.
- `processing v2` skips the legacy Kafka handoff only when `send_fulfillment=false`.
- Old pinned executions remain on their original build IDs.
- New executions route according to the Temporal Worker Deployment current/ramping version.

Required artifact model:

- Attendees must not edit files, copy files, or rebuild during the exercise.
- The v1 artifacts must contain the actual legacy behavior, not only the current source tree started
  with `TEMPORAL_WORKER_BUILD_ID=v1`.
- The workshop must provide deterministic v1/v2 worker artifacts or classpaths for:
  - `apps-workers:v1`
  - `apps-workers:v2`
  - `processing-workers:v1`
  - `processing-workers:v2`
- Each worker process must have an obvious name and log file:
  - `apps-v1.log`
  - `apps-v2.log`
  - `processing-v1.log`
  - `processing-v2.log`
- Startup commands should set build ID through environment variables, not by editing config files:

```bash
TEMPORAL_DEPLOYMENT_NAME=processing \
TEMPORAL_WORKER_BUILD_ID=v2 \
java -jar .workshop/artifacts/processing-workers-v2.jar
```

Recommended attendee command flow:

```bash
temporal worker deployment set-current-version \
  --deployment-name processing \
  --build-id v1 \
  --namespace processing

temporal worker deployment set-current-version \
  --deployment-name apps \
  --build-id v1 \
  --namespace apps
```

```bash
temporal worker deployment set-current-version \
  --deployment-name processing \
  --build-id v2 \
  --namespace processing
```

```bash
temporal worker deployment set-ramping-version \
  --deployment-name apps \
  --build-id v2 \
  --percentage 50 \
  --namespace apps
```

```bash
temporal worker deployment set-current-version \
  --deployment-name apps \
  --build-id v2 \
  --namespace apps
```

Hard code gap to close before scripting:

- Add `optional bool send_fulfillment = 3` to
  `ProcessOrderRequestExecutionOptions`.
- Regenerate Java and Python protobuf outputs if needed.
- Update `processing.Order` to use the routing slip with legacy-compatible default:
  absent `send_fulfillment` means `true`.
- Update `apps v2` to send `send_fulfillment=false`.
- Decide whether the existing `Workflow.getVersion("remove-kafka-fulfillment", ...)` branch is
  removed, retained only for replay safety, or converted into a compatibility shim.
- Add replay/compatibility tests before publishing exercise artifacts.

## TWC Demo Requirements

Recommendation: run the TWC demo instructor-local or in a dedicated instructor Codespace only.
Do not require every attendee Codespace to run the Kubernetes stack.

Reasons:

- Exercise 01 does not require Kubernetes.
- The current TWC demo spec says the Kubernetes/KinD manifests need to be brought current before the
  demo becomes final executable material.
- `scripts/kind/demo-up.sh` and `scripts/k3d/demo-up.sh` install cert-manager, TWC CRDs, the TWC
  chart, and Traefik, then build and load/import many Docker images. That is too much workshop risk
  for 40-50 attendee environments.
- The demo is observational. The learning objective is mapping manual Worker Deployment commands to
  TWC behavior, not having every attendee debug a local Kubernetes cluster.

Acceptable TWC demo modes:

1. Instructor-local KinD using current scripts after preflight validation.
2. Instructor Codespace with 8 core / 32 GB and a prewarmed k8s environment.
3. Recorded fallback video and captured CLI/k9s outputs if live infrastructure fails.

k3d validation path:

- k3d is a better candidate than KinD for a future Codespaces TWC path because k3d runs K3s, and
  K3s is explicitly lightweight.
- Local developer validation passed on 2026-04-29 with k3d `5.8.3`:
  - Created a single-node k3d cluster with K3s Traefik disabled.
  - Verified pods can reach a host Temporal dev server at `host.docker.internal:7233` when Temporal
    is bound to `0.0.0.0`.
  - Installed cert-manager, TWC CRDs, and the Temporal Worker Controller Helm chart.
  - Installed the repo Traefik manifest without conflicting with bundled K3s Traefik.
  - Imported local OMS images with `k3d image import`.
  - Applied the local app overlay successfully after rebuilding stale `enablements-api` artifacts.
  - Applied the existing processing `TemporalWorkerDeployment` local overlay.
  - Observed `TemporalConnectionHealthy=True`, `Ready=True`, and `RolloutComplete=True` for
    `temporal-oms-processing/processing-workers`.
  - Verified Temporal CLI saw the k3d-managed deployment with current build ID `v1-5cb8`.
- `scripts/k3d/*` now mirrors the KinD demo workflow without replacing KinD:
  - k3d cluster name: `temporal-oms`
  - kubeconfig path: `/tmp/k3d-config.yaml`
  - cluster create command disables bundled K3s Traefik with `--k3s-arg '--disable=traefik@server:0'`
  - local image transfer uses `k3d image import ... --cluster temporal-oms`
  - app overlays and processing `TemporalWorkerDeployment` overlays are the same Kustomize inputs
    as KinD.
- Codespaces validation is still required before adopting k3d for any participant-facing runbook.
- Before a polished k3d demo, add TWD manifests for `apps` and `fulfillment`; processing alone is
  not representative of the intended TWC topology.

Current parallel script surfaces:

| Surface | KinD path | k3d path |
|---|---|---|
| Full setup | `scripts/kind/demo-up.sh` | `scripts/k3d/demo-up.sh` |
| Full teardown | `scripts/kind/demo-down.sh` | `scripts/k3d/demo-down.sh` |
| Infrastructure | `scripts/kind/infra-up.sh`, `/tmp/kind-config.yaml` | `scripts/k3d/infra-up.sh`, `/tmp/k3d-config.yaml` |
| App deploy | `kind load docker-image ... --name temporal-oms` | `k3d image import ... --cluster temporal-oms` |
| Processing worker bump | `scripts/kind/deploy-processing-workers.sh` | `scripts/k3d/deploy-processing-workers.sh` |
| Status/tunnel/app removal | `scripts/kind/status.sh`, `scripts/kind/tunnel.sh`, `scripts/kind/app-down.sh` | `scripts/k3d/status.sh`, `scripts/k3d/tunnel.sh`, `scripts/k3d/app-down.sh` |
| Local Temporal target | `host.docker.internal:7233`; bind Temporal to `0.0.0.0` for Docker reachability | Same target; local spike validated this on Docker Desktop |
| Traefik | Repo installs Traefik explicitly | k3d disables bundled K3s Traefik before installing repo Traefik |

## Ports

Default attendee forwarded ports:

| Port | Label | Required | Visibility | Notes |
|---:|---|---|---|---|
| `8233` | Temporal UI | Yes | Private | Main observation surface |
| `8080` | Apps API | Yes | Private | Scenario order submission |
| `8050` | Enablements API | Yes | Private | Fixture-backed integrations |
| `8071` | Processing worker admin | Yes for Exercise 01 proof | Private | Kafka/no-Kafka proof endpoint |
| `8070` | Processing API | Recommended | Private | Needed by existing invalid-order support scripts |
| `7233` | Temporal gRPC | Optional | Private | Needed only for CLI access from outside the codespace |

Internal-only health and management ports:

- `9091` for `apps-api` management
- `9081` for `processing-api` management
- `9082` for `processing-workers` management
- `9050` for `enablements-api` management
- `9072` for fulfillment and enablements worker management; avoid same-port conflicts if both expose
  web management in local mode.

Do not make forwarded ports public for the workshop by default. Codespaces can share ports publicly
or within an organization, but this workshop does not need public API exposure.

## Secrets/API Keys

Exercise 01 should require no external API keys.

Recommended secret policy:

- `ANTHROPIC_API_KEY`:
  - Required only for later AI exercises if those exercises call Claude for real.
  - Provide through Codespaces user, repository, or organization secrets.
  - Do not write it to `.env.codespaces` or commit it anywhere.
- `OPENAI_API_KEY`:
  - Required only for later AI exercises or tooling if those paths call OpenAI APIs for real.
  - Provide through Codespaces user, repository, or organization secrets.
  - Do not write it to `.env.codespaces` or commit it anywhere.
- AI exercises:
  - `workshop-start.sh` should warn if absent and mark AI exercises unavailable, but still start
    Exercise 01.
- Temporal Cloud credentials:
  - Not required for attendee Codespaces.
  - Required only if the instructor TWC demo uses Temporal Cloud.
  - Keep in Codespaces secrets, local shell env, or gitignored config files. Never commit.

Important Codespaces constraint:

- Do not put secret-dependent work in Dockerfile builds or devcontainer features, because Codespaces
  secrets are runtime environment variables and are not available during build time.

## Caching/Prebuild Strategy

Use Codespaces prebuilds for workshop branches.

Prebuild should do:

```bash
cd java && mvn -DskipTests install
cd ../python && uv sync
```

Prebuild should also produce workshop artifacts if the selected v1/v2 artifact strategy requires
materializing jars under `.workshop/artifacts/`.

Do not rely on `postCreateCommand` for expensive dependency setup if the goal is prebuild caching.
GitHub prebuilds run `onCreateCommand` and `updateContentCommand`, but not `postCreateCommand`.

Recommended caching details:

- Pin Java, Maven, Python, uv, and Temporal CLI versions in the devcontainer.
- Keep Maven dependencies in the prebuild snapshot.
- Keep the Python `.venv` or uv-managed environment in the prebuild snapshot.
- Use `java -jar` for worker/API startup where possible, not `mvn spring-boot:run`.
- Avoid `mvn clean` during attendee startup.
- For k8s demo validation, build/load Docker images before the live session.
- Add a stale-artifact guard to prebuild or readiness: packaged jars/images must be newer than the
  compiled classes they contain, or the build must be rerun. The local k3d spike showed that stale
  nested Maven jars can produce confusing runtime failures that do not reproduce from source.

## Readiness Checks

`scripts/workshop-start.sh` should fail fast on hard blockers and print warnings for optional
features.

Hard checks:

- CPU, memory, and free disk meet the attendee minimum.
- Ports `7233`, `8233`, `8080`, `8050`, `8070`, and `8071` are free before startup.
- Java 21 is active.
- Maven is available.
- `uv` is available.
- `temporal` CLI is available and supports `worker deployment set-current-version`,
  `set-ramping-version`, and `describe`.
- `jq` and `curl` or `xh` are available.
- Temporal frontend health passes.
- Namespaces exist: `apps`, `processing`, `fulfillment`, and the enablements namespace.
- Nexus endpoints exist and target the expected namespace/task queue pairs.
- Fulfillment search attributes exist.
- Worker Deployment current versions are set for `apps` and `processing`.
- Pollers are visible for:
  - `apps` task queue in `apps`
  - `processing`, `commerce-app`, and `support` task queues in `processing`
  - `fulfillment` and `fulfillment-carriers` task queues in `fulfillment`
  - `agents` and `fulfillment-shipping` task queues in `fulfillment`
  - `integrations` and `enablements` task queues in the enablements namespace
- HTTP health probes pass for APIs and management ports.
- A smoke order can complete on the v1 path and produce an unambiguous Kafka proof.

Warnings:

- Missing `ANTHROPIC_API_KEY` means later AI exercises using live Claude calls are unavailable.
- Missing `OPENAI_API_KEY` means later AI exercises or tooling using live OpenAI calls are unavailable.
- Docker/kubectl/k3d/kind absent is acceptable for attendee exercises but not for instructor TWC
  demo validation.

Useful status output:

- Temporal UI URL.
- Apps API URL.
- Processing admin/Kafka proof URL.
- Active build IDs for `apps` and `processing`.
- Log file paths.
- Exact first Exercise 01 command.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| 2 core Codespaces are selected by default | Slow startup or OOM | Set `hostRequirements` to 4 cores / 16 GB / 64 GB |
| Java processes consume too much memory | OOM during workshop | Start from jars with explicit `JAVA_TOOL_OPTIONS` or per-process `-Xmx`; validate on 4 core / 16 GB |
| Dependency downloads happen during workshop | Timebox blown | Use Codespaces prebuilds; no Maven/uv install in `workshop-start.sh` |
| Current code does not match routing-slip Exercise 01 | Exercise scripts would teach the wrong mechanism | Close proto/code/test gap before exercise scripting |
| v1/v2 artifacts are ambiguous | Attendees cannot reason about build IDs | Prebuild immutable artifacts with names and logs that include `apps-v1`, `apps-v2`, `processing-v1`, `processing-v2` |
| Worker management ports collide | One or more local workers fail to start | Assign unique management ports or disable management web servers for workers that do not need HTTP health |
| Worker Deployment current version not set | Workers poll but tasks do not route | `setup-temporal-namespaces.sh` and readiness checks must explicitly set and describe current versions |
| Kafka proof endpoint is HTML/null ambiguous | Exercise validation confusion | Add or plan a machine-readable check before scripts, or make check script robust to current HTML |
| Python worker starts without AI key but later exercise needs it | Later exercise failure | Warn at startup; keep Exercise 01 independent |
| TWC demo fails live | Weak production bridge | Instructor preflight, prebuilt images, recorded fallback, and CLI transcript |
| k3d behaves differently from KinD | Demo blocked | Treat k3d as validation work, not initial dependency |
| `host.docker.internal` does not resolve from k3d/KinD in Codespaces | Kubernetes pods cannot reach local Temporal | Validate networking; prefer Temporal Cloud or in-cluster Temporal for k8s demo if needed |
| Stale Maven jars or Docker images do not match source | Runtime behavior differs between local source runs and k8s images | Prebuild from a clean reactor, verify packaged artifacts, and never require live rebuild debugging in Exercise 01 |
| TWD coverage exists only for processing | TWC demo does not match workshop topology | Add and validate TWD manifests for `apps`, `processing`, and `fulfillment` before relying on the demo |

## Open Questions

- What is the final v1/v2 artifact strategy for `apps-workers` and `processing-workers`?
- Should v1/v2 artifacts be built from git tags, Maven profiles, source snapshots, or a dedicated
  workshop packaging module?
- Should `processing.Order` retain the existing `Workflow.getVersion` branch for replay-only
  compatibility after the routing slip is added?
- Which Temporal CLI and Temporal dev server versions should be pinned?
- Should the enablements namespace remain `default`, or should the workshop use an explicit
  `enablements` namespace to reduce attendee confusion?
- Do later AI exercises require live Anthropic/OpenAI calls, or can they run with fixtures/mocks for
  all attendees?
- Can the organization provide `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` as Codespaces repository or
  organization secrets, or must attendees bring their own?
- Should the instructor Codespace demo prefer KinD or k3d after fresh Codespaces validation?
- For the k3d Codespaces path, should Temporal run on the devcontainer host, in the k3d cluster, or
  in Temporal Cloud?
- What should the `apps` and `fulfillment` `TemporalWorkerDeployment` names, build IDs, and rollout
  steps be?
- Should `scripts/setup-temporal-namespaces.sh` set build IDs to `v1` for workshop mode rather than
  `local`?

## Validation Plan

Phase 0 validation before exercise scripting:

- Verify the repo builds from a clean clone:
  - `cd java && mvn -DskipTests install`
  - `cd python && uv sync`
- Verify local Temporal dev server supports all Worker Deployment commands used in Exercise 01.
- Verify the routing-slip code gap is closed with tests.
- Verify side-by-side `apps v1`, `apps v2`, `processing v1`, and `processing v2` workers can poll
  concurrently with distinct build IDs.

Codespaces validation:

- Create a fresh Codespace from the workshop branch using the proposed devcontainer.
- Confirm the selected machine is at least 4 cores / 16 GB / 64 GB.
- Confirm prebuild creation includes Maven and uv dependency setup.
- Run `scripts/workshop-start.sh`.
- Complete Exercise 01 end-to-end in under 45 minutes with no rebuilds.
- Stop and restart the Codespace, then verify `scripts/workshop-start.sh` recovers cleanly.

Load validation:

- Run 10-20 concurrent or back-to-back orders during the `apps v2` ramp.
- Verify old and new orders complete.
- Verify old path creates Kafka proof records.
- Verify new path does not create Kafka proof records and does create `fulfillment.Order`.
- Verify `send_fulfillment=false` is visible in processing workflow input/history.

TWC validation:

- Preflight current KinD demo on instructor hardware if KinD remains the fallback path.
- Repeat the successful local k3d spike in a fresh environment:
  - cluster creation with K3s Traefik disabled
  - cert-manager
  - TWC install
  - image import or registry
  - host Temporal connectivity from pods
  - `TemporalWorkerDeployment` rollout
  - k9s observation flow
- Repeat the k3d validation inside a fresh Codespace on the proposed instructor machine size using
  [`k3d-remote-runbook.md`](./k3d-remote-runbook.md).
- Do not include k3d in attendee Exercise 01 instructions until this passes twice from a fresh
  Codespace.

## Implementation Phases

### Phase 1: Planning closure

- Approve this architecture split:
  - attendee local-process Codespaces
  - instructor-controlled TWC demo
- Decide v1/v2 artifact strategy.
- Validate both `scripts/kind/*` and `scripts/k3d/*` on a fresh machine.
- Pin Temporal CLI/server versions.

### Phase 2: Exercise 01 code alignment

- Add `send_fulfillment` to the proto contract.
- Update processing for legacy-compatible routing-slip behavior.
- Update apps v2 to send `send_fulfillment=false`.
- Add replay and compatibility tests.
- Build v1/v2 artifacts without attendee file copying.

### Phase 3: Codespaces foundation

- Add `.devcontainer/devcontainer.json` with 4 core / 16 GB / 64 GB host requirements.
- Add prebuild-friendly dependency setup.
- Add `scripts/workshop-start.sh`, `scripts/workshop-status.sh`, and `scripts/workshop-stop.sh`.
- Add readiness checks and log/PID conventions.

### Phase 4: Exercise scripting

- Add Exercise 01 scripts only after Phase 2 and Phase 3 are validated.
- Add robust proof scripts for Kafka path and fulfillment path.
- Dry-run with a fresh Codespace and time the exercise.

### Phase 5: TWC demo hardening

- Keep current KinD path supported.
- Validate `scripts/k3d/*` inside Codespaces.
- Prebuild images and prepare a recorded fallback.
- Keep this demo instructor-led unless k3d/KinD Codespaces validation is consistently reliable.
