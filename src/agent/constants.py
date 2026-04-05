from enum import Enum
from typing import List

CLIENT_CREDENTIALS_GRANT_TYPE: str = "client_credentials"
AUTH_SERVICE_M2M_TOKEN_ISSUE_PATH: str = "/internal/api/v1/m2m/token"

AGENT_HEARTBEAT_PATH = "/api/v1/agent/heartbeat"
AGENT_SUITE_PATH = "/api/v1/agent/suite"
AGENT_SUITE_ACK_PATH = "/api/v1/agent/suite/ack"
AGENT_SUITE_SCENARIO_PATH = "/api/v1/agent/suite/{suite_id}/scenario/{scenario_id}"
AGENT_CLUSTER_SNAPSHOT: str = "/api/v1/agent/cluster/snapshot"

DISCOVERY_k8_LEASE_NAME: str = "resilience-agent-snapshot-discovery-lease"


class AgentOAuthScopes(Enum):
    """Standardized OAuth scopes for agents"""

    # Events and metrics
    event_create = "res:oauth:scope:events:create"
    metrics_create = "res:oauth:scope:metrics:create"
    heartbeat = "res:oauth:scope:agent:heartbeat"
    config_read = "res:oauth:scope:agent:config:read"
    cluster_snapshot_upsert = "res:oauth:scope:agent:cluster:snapshot:upsert"

    @classmethod
    def values(cls) -> List[str]:
        return [scope.value for scope in cls]


class AgentHealthEnum(str, Enum):
    """Cluster Agent Status"""

    healthy = "healthy"
    degraded = "degraded"
