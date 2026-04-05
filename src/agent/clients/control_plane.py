import logging
from typing import Dict, Optional

from reslib.schemas.scenario import ResiliencyScenario

from agent.clients.base import BaseAPIClient
from agent.clients.token import AuthServiceClient
from agent.constants import (
    AGENT_CLUSTER_SNAPSHOT,
    AGENT_HEARTBEAT_PATH,
    AGENT_SUITE_ACK_PATH,
    AGENT_SUITE_PATH,
    AGENT_SUITE_SCENARIO_PATH,
    AgentHealthEnum,
)
from agent.schemas.config import AgentConfigModel
from agent.schemas.heartbeat import HeartbeatRequestModel, HeartbeatResponseModel
from agent.schemas.snapshot import ClusterSnapshotRequestModel
from agent.schemas.suite import ResiliencySuite

logger = logging.getLogger(__name__)


class ControlPlaneClient(BaseAPIClient):
    """
    Async client for interacting with the Control Plane API.

    Provides methods for:
    - Registering the agent
    - Sending periodic heartbeat signals
    - Fetching resiliency suite
    - Acknowledging suite
    """

    def __init__(self, config: AgentConfigModel, auth_service: AuthServiceClient):
        super().__init__(config)
        self.auth_service = auth_service

    @property
    def host(self) -> str:
        """
        Base URL of the control plane API.

        Returns:
            str: Host URL from the agent configuration.
        """
        return self.config.control_plane_api_host

    async def get_headers(self) -> Dict[str, str]:  # noqa
        """
        Return HTTP headers including authorization keys.

        Returns:
            dict: HTTP headers with 'Content-Type' and API keys.
        """
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
        """
        Send a heartbeat signal to indicate the agent is alive.

        Returns:
            Dict[str, Any]: Parsed JSON response from the control plane.
        """
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

    async def fetch_suite(self) -> Optional[ResiliencySuite]:
        """
        Fetch the next resiliency suite from the control plane.

        Returns:
            ResiliencySuite: Resiliency suite details, or an empty suite if
            none available.
        """
        logger.debug("Fetching resiliency suite from control plane")
        response: Dict = await self.request("GET", AGENT_SUITE_PATH)
        return ResiliencySuite(**response) if response else None

    async def ack_suite(self, suite_id: int) -> None:
        """Acknowledge that a resiliency suite has been received."""
        logger.info("Acknowledging suite with ID: %d", suite_id)
        await self.request(
            "POST",
            AGENT_SUITE_ACK_PATH,
            json={"id": suite_id},
        )
        return

    async def fetch_scenario(
        self, suite_id: int, scenario_id: int
    ) -> ResiliencyScenario:
        """
        Fetch the resiliency scenario information given id.

        Returns:
            ResiliencyScenario: Returns scenario instructions.
        """
        logger.debug("Fetching resiliency scenario from control plane")
        response: Dict = await self.request(
            "GET",
            AGENT_SUITE_SCENARIO_PATH.format(
                suite_id=suite_id, scenario_id=scenario_id
            ),
        )
        return ResiliencyScenario(**response)

    async def cluster_snapshot(self, payload: ClusterSnapshotRequestModel) -> None:
        """
        Send a cluster snapshot to the control plane.

        This method submits the current Kubernetes cluster state to the control
        plane via a POST request. The snapshot includes a unique synchronization
        UUID and the state of all namespaces, which can be used for reconciliation,
        auditing, or state tracking.
        """
        logger.debug("Cluster snapshot from control plane")
        await self.request(
            "POST",
            AGENT_CLUSTER_SNAPSHOT,
            json=payload.model_dump(exclude_none=True, mode="json"),
        )
        return None
