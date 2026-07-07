# ResilOps Agent

[![Tests](https://github.com/resilops/resilops-agent/actions/workflows/test.yaml/badge.svg)](https://github.com/resilops/resilops-agent/actions/workflows/test.yaml)
[![codecov](https://codecov.io/gh/resilops/resilops-agent/graph/badge.svg)](https://codecov.io/gh/resilops/resilops-agent)
[![Release Agent](https://github.com/resilops/resilops-agent/actions/workflows/release.yaml/badge.svg)](https://github.com/resilops/resilops-agent/actions/workflows/release.yaml)
[![Release](https://img.shields.io/github/v/release/resilops/resilops-agent)](https://github.com/resilops/resilops-agent/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/resilops/resilops-agent/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://github.com/resilops/resilops-agent/blob/main/pyproject.toml)

`resilops-agent` is the Kubernetes-side runtime for ResilOps resilience
validation. It runs inside a customer cluster, receives scenario work from the
ResilOps control plane, executes that work through
[`resilience-lib`](../resilience-lib), and emits structured telemetry back to
the platform.

This repository is public because the execution model, RBAC scope, and cluster-side
behavior should be inspectable. Contributions are welcome from engineers working
on Kubernetes reliability, platform engineering, SRE, and release validation
workflows.

## What This Agent Does

The agent is responsible for the cluster-local parts of a resilience validation
run:

- heartbeats to the control plane
- polling for queued resilience scenario claims
- fetching and executing scenario runs through `resilience-lib`
- namespace discovery snapshots
- leader election through Kubernetes `Lease` resources
- forwarding event and metric telemetry through a Fluent Bit sidecar

In practice, this repo is the delivery and runtime layer around
`resilience-lib`. The library defines how scenarios execute. This agent handles
how that runtime is deployed, configured, authenticated, and operated inside a
cluster.

## How This Fits In The ResilOps Stack

The public ResilOps repositories are split by responsibility:

- `resilience-lib`: the scenario runtime and validation engine
- `resilops-agent`: the in-cluster worker that executes that runtime
- `resilience-web`: the web application and control-plane-facing UI

That separation is intentional. It keeps the validation logic, the cluster
runtime, and the product surface independently inspectable and easier to
contribute to.

## How This Differs From Chaos Engineering

This project uses some of the same mechanisms as chaos engineering, but it is
not the same discipline.

`resilops-agent` exists to run controlled, scenario-driven resilience
validation. The goal is not broad fault exploration or random disruption. The
goal is to gather repeatable evidence that a workload satisfies recovery and
reliability expectations with a bounded blast radius.

That distinction shows up in a few ways:

- runs are driven by explicit scenarios rather than open-ended experiments
- execution is gated by guardrails implemented in `resilience-lib`
- rollback and recovery verification are part of the expected workflow
- results are meant to support release readiness, drift detection, and
  operational confidence
- cluster permissions are scoped to the specific validation actions the agent
  must perform

If your goal is unrestricted production fault injection, large-scale game days,
or exploratory chaos programs, that is adjacent work but not the focus of this
repository.

## Repository Layout

- `src/agent/`: application code
- `helm/agent/`: Helm chart used to deploy the agent
- `mockserver/`: mock control plane for local development
- `examples/`: example workloads and scenario payloads
- `docker/`: local image build inputs

## Requirements

- Python `>=3.12,<4.0`
- Poetry
- a Kubernetes cluster for runtime testing
- Helm for chart rendering and installation
- access to a checkout of `../resilience-lib` for local development workflows

## Installation And Deployment

The chart is published as an OCI artifact:

```text
oci://ghcr.io/resilops/charts/agent
```

Example install:

```bash
helm install agent \
  oci://ghcr.io/resilops/charts/agent \
  --version 1.0.0 \
  --namespace resilops \
  --create-namespace \
  --set existingSecret.name=resilops-agent-secrets \
  --set-string envVar.data.RESILOPS_AGENT_CONFIG_VERSION=1.0.0 \
  --set 'rbac.namespaced.namespaces={nginx,http-echo}'
```

Example upgrade:

```bash
helm upgrade agent \
  oci://ghcr.io/resilops/charts/agent \
  --version 1.0.0 \
  --namespace resilops
```

Cluster operators still need to provide:

- OAuth client credentials in a Kubernetes secret
- the control plane URL for the target region
- the auth service URL for the target region
- the target namespaces the agent is allowed to operate in

## Configuration

Runtime settings are loaded from environment variables prefixed with
`RESILOPS_AGENT_`.

Required settings:

- `RESILOPS_AGENT_AUTH_SERVICE_HOST`
- `RESILOPS_AGENT_AUTH_SERVICE_CLIENT_ID`
- `RESILOPS_AGENT_AUTH_SERVICE_CLIENT_SECRET`
- `RESILOPS_AGENT_CONTROL_PLANE_API_HOST`
- `RESILOPS_AGENT_NAMESPACE`
- `RESILOPS_AGENT_TARGET_NAMESPACES`
- `RESILOPS_AGENT_CONFIG_VERSION`

Operational settings:

- `RESILOPS_AGENT_HEARTBEAT_INTERVAL` default `30`
- `RESILOPS_AGENT_RUNNER_INTERVAL` default `5`
- `RESILOPS_AGENT_RESILIENCY_SCENARIO_POLL_INTERVAL` default `60`
- `RESILOPS_AGENT_NAMESPACE_SNAPSHOT_INTERVAL` default `10800`

Logging settings:

- `LOG_LEVEL` default `INFO`
- `LOG_FILE` default `/var/log/agent/agent.log`
- `LOG_MAX_MB` default `50`
- `LOG_BACKUP_COUNT` default `3`

See `helm/agent/values.yaml` for chart defaults, region mappings, sidecar
configuration, and RBAC settings.

## Kubernetes Permissions

The Helm chart configures RBAC for:

- pods, including delete and patch operations
- pod evictions
- services
- EndpointSlices
- pod exec
- events
- deployments, including patch operations
- HorizontalPodAutoscalers
- PodDisruptionBudgets
- pod metrics from `metrics.k8s.io`
- `coordination.k8s.io` `leases` in the agent namespace

The intention is not blanket cluster administration. The permissions are shaped
around the specific disruption, observation, and recovery checks required by
the current validation workflows.

## Local Development

This repository includes a local workflow for testing the agent against a mock
control plane.

Useful commands:

- `make lib`
- `make build`
- `make secrets`
- `make up`
- `make down`
- `make logs`
- `make forward`
- `make examples-up`
- `make examples-down`
- `make tests`

Supporting components:

- `mockserver/deployment.yaml`: mock control plane for local testing
- `examples/`: demo workloads and scenario payloads

## Contributing

Contributions are welcome, especially in areas such as:

- Kubernetes runtime hardening
- Helm chart improvements
- RBAC minimization and review
- telemetry and operability
- local development ergonomics
- documentation and examples

Before opening a larger pull request, start with an issue that explains the
problem, the proposed change, and any operational tradeoffs. That keeps changes
aligned across `resilops-agent`, `resilience-lib`, and the web/control-plane
surface.

When contributing:

- keep changes scoped to the agent or chart unless a cross-repo change is
  clearly required
- call out RBAC changes explicitly
- document behavior changes that affect operators or cluster permissions
- include tests where the change touches runtime behavior

## Related Files

- `helm/agent/values.yaml`: chart defaults and region endpoint mappings
- `.github/workflows/release.yaml`: chart publication workflow
- `DISTRIBUTION.md`: current packaging and delivery notes
- `LICENSE`: repository license terms

## License

Apache-2.0. See [LICENSE](LICENSE).
