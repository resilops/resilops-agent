# Resilience Agent

`resilience-agent` is the Kubernetes-side runtime for ResilOps resiliency
validation. It runs in a customer Kubernetes cluster, communicates with the
ResilOps control plane, executes resiliency scenarios through `resilience-lib`,
and emits structured event and metric telemetry.

This repository is proprietary software owned by ResilOps.

## What the agent does

- Sends periodic heartbeats to the control plane.
- Polls for queued resiliency scenario claims.
- Fetches and executes scenario runs through `resilience-lib`.
- Captures namespace discovery snapshots.
- Uses Kubernetes `Lease` resources for leader election.
- Forwards telemetry through a Fluent Bit sidecar.

## Repository roles

- `src/agent/`: the real application.
- `helm/agent/`: the publishable Helm chart for the agent.
- `mockserver/`: supporting mock control plane for local development only.
- `examples/`: supporting demo workloads and scenario payloads only.

## Release workflow

The intended release flow is:

1. Create a Git tag and GitHub release.
2. Run the chart release workflow.
3. Publish the Helm chart to GHCR as an OCI artifact.
4. Customers install the published chart.

The chart release workflow packages `helm/agent` and publishes it to:

```text
oci://ghcr.io/resilops/charts/agent
```

## Customer chart usage

The published agent chart is publicly readable from GHCR. Customers install it
directly from the OCI registry.

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

Customers still need to provide:

- OAuth client credentials in a Kubernetes secret.
- The control plane URL for their region.
- The auth service URL for their region.
- The target namespaces the agent is allowed to operate in.

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

## Kubernetes permissions

The agent chart configures RBAC for:

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

## Local development

Local development support in this repository exists for testing the agent, not
for customer deployment.

Supporting components:

- `mockserver/deployment.yaml`: mock control plane for local testing
- `examples/`: demo workloads and scenario payloads

Useful commands:

- `make build`
- `make secrets`
- `make up`
- `make down`
- `make logs`
- `make forward`
- `make examples-up`
- `make examples-down`

## Related files

- `helm/agent/values.yaml`: chart defaults and region endpoint mappings
- `.github/workflows/release-chart.yml`: manual chart publication workflow
- `LICENSE`: proprietary license terms
