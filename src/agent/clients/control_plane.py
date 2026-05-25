import logging
from typing import Dict, Optional

from pydantic import UUID4

from agent.clients.base import BaseAPIClient
from agent.clients.token import AuthServiceClient
from agent.constants import (
    AGENT_CLAIM_SET_ACK_PATH,
    AGENT_CLAIM_SETS_PATH,
    AGENT_CLUSTER_SNAPSHOT,
    AGENT_HEARTBEAT_PATH,
    AGENT_SCENARIO_RUN_PATH,
    AgentHealthEnum,
    ScenarioClaimStatus,
)
from agent.schemas.config import AgentConfig
from agent.schemas.heartbeat import HeartbeatRequest, HeartbeatResponse
from agent.schemas.scenario import ScenarioClaimSet, ScenarioRun
from agent.schemas.snapshot import ClusterSnapshot

logger = logging.getLogger(__name__)


class ControlPlaneClient(BaseAPIClient):
    """Client for control plane API operations used by the agent."""

    def __init__(self, config: AgentConfig, auth_service: AuthServiceClient):
        super().__init__(config)
        self.auth_service = auth_service

    @property
    def host(self) -> str:
        """Return the control plane base URL."""
        return self.config.control_plane_api_host

    async def get_headers(self) -> Dict[str, str]:  # noqa
        """Return authenticated request headers for control plane calls."""
        token_response = await self.auth_service.get_m2m_token()
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token_response.access_token}",
        }

    async def send_heartbeat(
        self,
        health: AgentHealthEnum = AgentHealthEnum.healthy,
        reason: Optional[str] = None,
    ) -> HeartbeatResponse:
        """Send the current agent heartbeat to the control plane."""
        logger.debug("Sending heartbeat")
        payload = HeartbeatRequest(
            health=health,
            version=self.config.app_version,
            config_version=self.config.config_version,
            reason=reason if health != AgentHealthEnum.healthy else None,
        )
        response: Dict = await self.request(
            "POST",
            AGENT_HEARTBEAT_PATH,
            json=payload.model_dump(mode="json"),
        )
        return HeartbeatResponse(**response)

    async def fetch_scenario_claim_set(self) -> Optional[ScenarioClaimSet]:
        """Return the next available scenario claim set, if one exists."""
        logger.debug("Fetching claim set from control plane")
        response = await self.request("GET", AGENT_CLAIM_SETS_PATH)

        claim_set = ScenarioClaimSet(**response[0]) if response else None
        if claim_set and claim_set.status == ScenarioClaimStatus.pending:
            return claim_set

        return None

    async def ack_scenario_claim_set(
        self,
        claim_set_id: UUID4,
    ) -> None:
        """Acknowledge receipt of a scenario claim set."""
        logger.info("Acknowledging scenario claim set with ID: %s", claim_set_id)
        await self.request(
            "POST",
            AGENT_CLAIM_SET_ACK_PATH.format(claim_set_id=str(claim_set_id)),
        )
        return

    async def fetch_scenario_run(self, scenario_id: int, run_id: int) -> ScenarioRun:
        """Fetch a run configuration"""
        logger.debug("Fetching resiliency scenario run from control plane")
        response: Dict = await self.request(
            "GET",
            AGENT_SCENARIO_RUN_PATH.format(scenario_id=scenario_id, run_id=run_id),
        )
        return ScenarioRun(**response)

    async def publish_cluster_snapshot(self, payload: ClusterSnapshot) -> None:
        """Send a namespace discovery snapshot to the control plane."""
        logger.debug("Sending cluster snapshot to control plane")
        await self.request(
            "POST",
            AGENT_CLUSTER_SNAPSHOT,
            json=payload.model_dump(exclude_none=True, mode="json"),
        )
        return None
