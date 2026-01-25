import logging
from typing import Dict, Optional

from agent.clients.base import BaseAPIClient
from agent.schemas.heartbeat import HeartbeatResponseModel
from agent.schemas.suite import ResiliencyScenario, ResiliencySuite

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

    @property
    def host(self) -> str:
        """
        Base URL of the control plane API.

        Returns:
            str: Host URL from the agent configuration.
        """
        return self.config.control_plane_api_host

    async def send_heartbeat(self) -> HeartbeatResponseModel:
        """
        Send a heartbeat signal to indicate the agent is alive.

        Returns:
            Dict[str, Any]: Parsed JSON response from the control plane.
        """
        logger.debug("Sending heartbeat")
        response: Dict = await self.request("GET", "/api/v1/agent/heartbeat")
        return HeartbeatResponseModel(**response)

    async def fetch_suite(self) -> Optional[ResiliencySuite]:
        """
        Fetch the next resiliency suite from the control plane.

        Returns:
            ResiliencySuite: Resiliency suite details, or an empty suite if
            none available.
        """
        logger.debug("Fetching resiliency suite from control plane")
        response: Dict = await self.request("GET", "/api/v1/agent/suite")
        return ResiliencySuite(**response) if response else None

    async def ack_suite(self, suite_id: int) -> None:
        """Acknowledge that a resiliency suite has been received."""
        logger.info("Acknowledging suite with ID: %d", suite_id)
        await self.request("POST", "/api/v1/agent/suite/ack", json={"id": suite_id})
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
            "GET", f"/api/v1/agent/suite/{suite_id}/scenario/{scenario_id}"
        )
        return ResiliencyScenario(**response)
