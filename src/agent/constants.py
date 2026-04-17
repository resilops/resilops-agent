from enum import Enum

CLIENT_CREDENTIALS_GRANT_TYPE: str = "client_credentials"
AUTH_SERVICE_M2M_TOKEN_ISSUE_PATH: str = "/api/v1/m2m/token"

AGENT_HEARTBEAT_PATH = "/api/v1/agent/heartbeat"
AGENT_CLAIMS_PATH = "/api/v1/agent/scenario-queue/claims"
AGENT_CLAIM_ACK_PATH = "/api/v1/agent/scenario-claims/{claim_id}/ack"
AGENT_SCENARIO_PATH = "/api/v1/agent/scenario/{scenario_id}"
AGENT_CLUSTER_SNAPSHOT: str = "/api/v1/agent/snapshots/cluster"

DISCOVERY_K8S_LEASE_NAME: str = "resilience-agent-snapshot-discovery-lease"


class AgentOAuthScopes(Enum):
    """OAuth scopes required by the agent."""

    # Events and metrics
    event_create = "res:oauth:scope:events:create"
    metrics_create = "res:oauth:scope:metrics:create"
    heartbeat = "res:oauth:scope:agent:heartbeat"
    config_read = "res:oauth:scope:agent:config:read"
    cluster_snapshot_upsert = "res:oauth:scope:agent:cluster:snapshot:upsert"

    @classmethod
    def scopes(cls) -> str:
        """Return the scopes as a space-delimited OAuth scope string."""
        return " ".join(scope.value for scope in cls)


class AgentHealthEnum(str, Enum):
    """Health values accepted by the control plane heartbeat endpoint."""

    healthy = "healthy"
    degraded = "degraded"


class ResiliencyScenarioClaimStatusEnum(str, Enum):
    """Resiliency scenario claims status."""

    pending = "pending"
    acknowledged = "acknowledged"
