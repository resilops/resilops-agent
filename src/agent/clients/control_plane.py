import logging
from typing import Dict, Optional

from agent.clients.base import BaseAPIClient
from agent.clients.token import AuthServiceClient
from agent.constants import (
    AGENT_CLAIM_ACK_PATH,
    AGENT_CLAIMS_PATH,
    AGENT_CLUSTER_SNAPSHOT,
    AGENT_HEARTBEAT_PATH,
    AGENT_SCENARIO_PATH,
    AgentHealthEnum,
    ResiliencyScenarioClaimStatusEnum,
)
from agent.schemas.config import AgentConfigModel
from agent.schemas.heartbeat import HeartbeatRequestModel, HeartbeatResponseModel
from agent.schemas.scenario import ResiliencyScenario, ResiliencyScenarioClaim
from agent.schemas.snapshot import ClusterSnapshotRequestModel

logger = logging.getLogger(__name__)


class ControlPlaneClient(BaseAPIClient):
    """Client for control plane API operations used by the agent."""

    def __init__(self, config: AgentConfigModel, auth_service: AuthServiceClient):
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
    ) -> HeartbeatResponseModel:
        """Send the current agent heartbeat to the control plane."""
        logger.debug("Sending heartbeat")
        payload = HeartbeatRequestModel(
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
        return HeartbeatResponseModel(**response)

    async def fetch_scenario_claim(self) -> Optional[ResiliencyScenarioClaim]:
        """Return the next available scenario claim, if one exists."""
        logger.debug("Fetching claim from control plane")
        response = await self.request("GET", AGENT_CLAIMS_PATH)

        claim = ResiliencyScenarioClaim(**response[0]) if response else None
        if claim and claim.status == ResiliencyScenarioClaimStatusEnum.pending:
            return claim

        return None

    async def ack_scenario_claim(self, claim_id: int) -> None:
        """Acknowledge receipt of a scenario claim."""
        logger.info("Acknowledging scenario with ID: %d", claim_id)
        await self.request(
            "POST",
            AGENT_CLAIM_ACK_PATH.format(claim_id=claim_id),
        )
        return

    async def fetch_scenario(self, scenario_id: int) -> ResiliencyScenario:
        """Fetch a scenario definition by ID."""
        logger.debug("Fetching resiliency scenario from control plane")
        response: Dict = await self.request(
            "GET", AGENT_SCENARIO_PATH.format(scenario_id=scenario_id)
        )
        return ResiliencyScenario(**response)

    async def publish_cluster_snapshot(
        self, payload: ClusterSnapshotRequestModel
    ) -> None:
        """Send a namespace discovery snapshot to the control plane."""
        logger.debug("Sending cluster snapshot to control plane")
        await self.request(
            "POST",
            AGENT_CLUSTER_SNAPSHOT,
            json=payload.model_dump(exclude_none=True, mode="json"),
        )
        return None
