# Resilience Agent

`resilience-agent` is the Kubernetes-side runtime for Resilty.io resiliency
validation. It runs inside or against a Kubernetes cluster, reports agent
health to the Resilty control plane, discovers namespace state, claims queued
resiliency scenarios, executes them through `resilience-lib`, and emits
structured event and metric telemetry.

The package exposes a console command named `resilience-agent` and is designed
to run as a long-lived async worker process.

## What the agent does

- Sends periodic heartbeats to the control plane with the running app version,
  config version, and health state.
- Polls the control plane for pending resiliency scenario claims.
- Acknowledges and locally queues one claim at a time.
- Fetches the full scenario run configuration and executes it through
  `resilience-lib`.
- Captures Kubernetes namespace discovery snapshots and publishes them to the
  control plane.
- Uses Kubernetes `Lease` resources for leader election so only one replica
  performs snapshot discovery at a time.
- Writes JSON logs for agent events and `resilience-lib` metrics. The Helm
  deployment includes a Fluent Bit sidecar that forwards event and metric logs
  to the control plane ingestion endpoints.

## Repository layout

```text
.
|-- docker/                         Dockerfiles for the agent, mock server, and demo nginx image
|-- examples/                       Kubernetes demo workloads and scenario payloads
|   |-- http-echo.yaml
|   |-- nginx-hpa.yaml
|   |-- pod_kill/
|   `-- pod_scaling/
|-- helm/                           Values used with the shared application Helm chart
|   |-- agent/
|   `-- controlplane/
|-- local-libs/resilience-lib/      Local editable copy of the scenario execution library
|-- mockserver/                     FastAPI mock control plane for local development
|-- src/agent/                      Agent package
|   |-- clients/                    Auth and control-plane API clients
|   |-- core/                       Worker base classes, lifecycle, manager, leader election
|   |-- handlers/                   Scenario, snapshot, state, and telemetry handlers
|   |-- schemas/                    Pydantic request, response, and state models
|   `-- workers/                    Heartbeat, scheduler, runner, and snapshot workers
|-- src/tests/                      Pytest test suite
|-- Makefile                        Local build, Helm, and demo workflow commands
|-- pyproject.toml                  Poetry package metadata and tool configuration
`-- poetry.lock
```

## Runtime architecture

The entry point is `agent.entrypoint:run`.

At startup the agent:

1. Configures JSON logging.
2. Loads `AgentConfig` from `RESILTY_AGENT_` environment variables.
3. Builds an authenticated `ControlPlaneClient`.
4. Creates shared in-memory agent state.
5. Creates a Kubernetes lease-based leader election helper.
6. Starts the background workers through `WorkerManager`.
7. Waits for `SIGINT` or `SIGTERM` and shuts workers down gracefully.

### Workers

| Worker | Class | Default interval | Purpose |
| --- | --- | ---: | --- |
| Heartbeat | `HeartbeatWorker` | 30 seconds | Posts health, app version, and config version to `/api/v1/agent/heartbeat`. |
| Scenario scheduler | `ScenarioSchedulerWorker` | 60 seconds | Polls `/api/v1/agent/scenario-queue/claims`, acknowledges a pending claim, and queues it locally. |
| Scenario executor | `ScenarioRunnerWorker` | 5 seconds | Runs the queued scenario through `resilience-lib` and emits execution events. |
| Namespace snapshot | `SnapshotWorker` | 3 hours after startup retries | Acquires or renews the Kubernetes leader lease, discovers target namespaces in batches, and publishes cluster snapshots. |

The snapshot worker retries quickly during startup: up to five attempts at a
20-second interval before switching to the configured snapshot interval.

## Configuration

Runtime settings are loaded with `pydantic-settings` from environment variables
prefixed with `RESILTY_AGENT_`.

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `RESILTY_AGENT_AUTH_SERVICE_HOST` | Yes | None | Base URL for the OAuth/M2M token service. |
| `RESILTY_AGENT_AUTH_SERVICE_CLIENT_ID` | Yes | None | OAuth client ID used by the agent. |
| `RESILTY_AGENT_AUTH_SERVICE_CLIENT_SECRET` | Yes | None | OAuth client secret used by the agent. |
| `RESILTY_AGENT_CONTROL_PLANE_API_HOST` | Yes | None | Base URL for the Resilty control plane API. |
| `RESILTY_AGENT_NAMESPACE` | Yes | None | Namespace where the agent runs and stores its leader-election lease. |
| `RESILTY_AGENT_TARGET_NAMESPACES` | Yes | None | Comma-separated list of Kubernetes namespaces the agent may discover and operate against. |
| `RESILTY_AGENT_CONFIG_VERSION` | Yes | None | Control-plane supplied configuration version or hash. |
| `RESILTY_AGENT_HEARTBEAT_INTERVAL` | No | `30` | Seconds between heartbeat attempts. Minimum: `30`. |
| `RESILTY_AGENT_RUNNER_INTERVAL` | No | `5` | Seconds between local runner queue checks. Minimum: `5`. |
| `RESILTY_AGENT_RESILIENCY_SCENARIO_POLL_INTERVAL` | No | `60` | Seconds between control-plane claim polling attempts. Minimum: `60`. |
| `RESILTY_AGENT_NAMESPACE_SNAPSHOT_INTERVAL` | No | `10800` | Seconds between namespace snapshots after startup. Minimum: `10800`. |

Logging settings are read without the `RESILTY_AGENT_` prefix:

| Variable | Default | Description |
| --- | --- | --- |
| `LOG_LEVEL` | `INFO` | Log level for the `agent` logger. |
| `LOG_FILE` | `/var/log/agent/agent.log` | File path for rotating JSON logs. |
| `LOG_MAX_MB` | `50` | Max size of one log file before rotation. |
| `LOG_BACKUP_COUNT` | `3` | Number of rotated log files to retain. |

For local source runs, set `LOG_FILE` to a writable path such as
`./agent.log` unless `/var/log/agent` already exists and is writable.

## Control plane API usage

The agent talks to these control plane and auth endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/m2m/token` | Fetch an M2M access token with the client credentials grant. |
| `POST` | `/api/v1/agent/heartbeat` | Report agent health and versions. |
| `GET` | `/api/v1/agent/scenario-queue/claims` | Fetch pending scenario claims. |
| `POST` | `/api/v1/agent/scenario-claims/{claim_id}/ack` | Acknowledge a claimed scenario. |
| `GET` | `/api/v1/agent/scenarios/{scenario_id}/runs/{run_id}` | Fetch the full scenario run configuration. |
| `POST` | `/api/v1/agent/snapshots/cluster` | Publish a namespace discovery snapshot. |

The Fluent Bit sidecar forwards telemetry logs to:

- `POST /api/v1/agent/events`
- `POST /api/v1/agent/metrics`

## OAuth scopes

The agent requests these OAuth scopes when fetching an M2M token:

```text
res:oauth:scope:events:create
res:oauth:scope:metrics:create
res:oauth:scope:agent:heartbeat
res:oauth:scope:agent:config:read
res:oauth:scope:agent:cluster:snapshot:upsert
res:oauth:scope:agent:claims:read
res:oauth:scope:agent:claims:ack
res:oauth:scope:agent:scenario_run_config:read
```

## Kubernetes permissions

The Helm values define RBAC for the agent.

For target namespaces, the agent needs access to:

- Pods, including delete operations for pod termination scenarios.
- Services.
- Pod exec.
- Events.
- Deployments.
- HorizontalPodAutoscalers.
- PodDisruptionBudgets.
- Pod metrics from `metrics.k8s.io`.

In the agent namespace, it needs access to `coordination.k8s.io` `leases` for
leader election.

## Local development

### Prerequisites

- Python 3.12 or newer.
- Poetry 2.x.
- Docker.
- Kubernetes tooling for deployment workflows: `kubectl`, `helm`, and
  optionally `minikube`.
- Access to the shared Helm app chart expected by the Makefile at
  `../helm-charts/app`.
- A local or vendored `resilience-lib` checkout. The Makefile copies it from
  `../resilience-lib` into `./local-libs/resilience-lib`.

### Install dependencies

```bash
poetry install --with local
```

If you want to refresh the vendored local library first:

```bash
make lib
poetry install --with local
```

### Run tests

```bash
poetry run pytest
```

With coverage:

```bash
poetry run pytest --cov=agent
```

### Run formatting and checks

The repository includes pre-commit hooks for YAML checks, end-of-file fixes,
trailing whitespace, Black, isort, and flake8.

```bash
pre-commit run --all-files
```

## Running the agent from source

Set the required environment variables and run the console script:

```bash
export RESILTY_AGENT_AUTH_SERVICE_HOST=http://localhost:8000
export RESILTY_AGENT_AUTH_SERVICE_CLIENT_ID=local-client
export RESILTY_AGENT_AUTH_SERVICE_CLIENT_SECRET=local-secret
export RESILTY_AGENT_CONTROL_PLANE_API_HOST=http://localhost:8000
export RESILTY_AGENT_NAMESPACE=resiltyio
export RESILTY_AGENT_TARGET_NAMESPACES=nginx,http-echo
export RESILTY_AGENT_CONFIG_VERSION=local
export LOG_FILE=./agent.log

poetry run resilience-agent
```

The agent loads Kubernetes configuration automatically. Inside a cluster it uses
in-cluster config; outside a cluster it falls back to the local kubeconfig.

## Mock control plane

`mockserver/` contains a FastAPI app that implements the auth, heartbeat,
snapshot, claim, scenario, event, and metric endpoints needed for local
development.

Run it locally:

```bash
cd mockserver
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

Queue an example scenario:

```bash
curl -X POST http://localhost:8000/api/v1/scenario-queue/items \
  -H 'Content-Type: application/json' \
  --data @examples/pod_kill/scenario.json
```

The mock server stores one queued scenario in memory.

## Docker images

Build the local agent and mock control plane images for Minikube:

```bash
make build
```

This target:

1. Copies `../resilience-lib` into `./local-libs/resilience-lib`.
2. Points Docker at Minikube with `minikube docker-env`.
3. Builds `resilience-agent:local`.
4. Builds `resilience-agent-cp:local`.

The production agent image installs package dependencies without the local
dependency group. The `local` Docker stage copies `local-libs/resilience-lib`
and installs with the `local` dependency group.

## Helm and Kubernetes workflow

The Makefile expects a reusable app chart at `../helm-charts/app`.

Render the agent and local control-plane charts:

```bash
make chart
```

Create or update the local Kubernetes secret from `.env`:

```bash
make secrets
```

The `.env` file should define:

```bash
OAUTH_CLIENT_ID=...
OAUTH_CLIENT_SECRET=...
```

Deploy the mock control plane and agent:

```bash
make up
```

Port-forward the control plane service:

```bash
make forward
```

Stream agent logs:

```bash
make logs
```

Stream Fluent Bit sidecar logs:

```bash
make logs-fluentbit
```

Remove the local releases:

```bash
make down
```

The default local settings deploy into the `resiltyio` namespace, use
`resilience-agent:local` and `resilience-agent-cp:local`, and target the
`nginx` and `http-echo` namespaces.

## Demo workloads and scenarios

### Nginx with HPA

Deploy:

```bash
make nginx-up
```

Delete:

```bash
make nginx-down
```

This uses `examples/nginx-hpa.yaml` and the local `resiltyio-nginx:local`
image. The related scenario files are:

- `examples/pod_kill/scenario.json`
- `examples/pod_scaling/scenario.json`

### HTTP echo with HPA

Deploy:

```bash
make http-up
```

Delete:

```bash
make http-down
```

This uses `examples/http-echo.yaml` and the public `hashicorp/http-echo:1.0`
image.

## Scenario execution model

Scenario payloads contain:

- `template`: workload-specific inputs such as namespace, deployment name,
  quantity, HPA metric settings, and thresholds.
- `steps`: ordered guardrail, action, and rollback steps.
- `observer`: telemetry collection configuration, such as endpoint latency
  measurements.

The agent does not implement those scenario primitives directly. It fetches the
scenario run from the control plane and passes the scenario config to
`reslib.runtime.scenario.execute_resilience_scenario`.

## Telemetry

Agent telemetry is emitted as JSON logs. Each event includes:

- `type`: `event`
- `source`: `agent`
- `event_name`
- `ingest_id`
- optional `run_id`
- optional `data`
- optional `error`

Agent event names include:

- `res:agent:event:scenario:queued`
- `res:agent:event:scenario:executing`
- `res:agent:event:scenario:execution:success`
- `res:agent:event:scenario:execution:failed`
- `res:agent:event:discovery:success`
- `res:agent:event:discovery:failed`

Metrics emitted by `resilience-lib` are forwarded through the same log path by
the `RunTelemetry` adapter and separated by Fluent Bit based on `type=metric`.

## Makefile reference

| Target | Description |
| --- | --- |
| `make help` | Show available targets. |
| `make lib` | Copy `../resilience-lib` into `./local-libs/resilience-lib`. |
| `make chart` | Render the agent and local control-plane Helm manifests. |
| `make build` | Build local Docker images in the Minikube Docker environment. |
| `make secrets` | Create or update the Kubernetes secret from `.env`. |
| `make up` | Deploy the mock control plane and agent with Helm. |
| `make down` | Uninstall the local Helm releases. |
| `make forward` | Port-forward the local control-plane service to `localhost:8000`. |
| `make logs` | Stream logs from the agent container. |
| `make logs-fluentbit` | Stream logs from the Fluent Bit sidecar. |
| `make nginx-up` | Build and deploy the local nginx HPA demo workload. |
| `make nginx-down` | Delete the nginx HPA demo workload. |
| `make http-up` | Deploy the HTTP echo HPA demo workload. |
| `make http-down` | Delete the HTTP echo HPA demo workload. |

## Notes and caveats

- `README.md` was previously empty, so this document is based on the current
  source tree, Helm values, Dockerfiles, examples, and Makefile.
- The repository includes a checked-in `.env`; keep real credentials out of git
  and rotate any credential that may have been committed.
- `examples/pod_kill/REAME.md` appears to be misspelled and may be intended to
  be `README.md`.
- The test files currently reference some legacy helper/logging names. If tests
  fail, compare them against the current implementations in `agent.helper` and
  `agent.logging`.
