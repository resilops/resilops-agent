import logging
from typing import Dict

from agent.clients.base import BaseAPIClient
from agent.models.fault import FaultPlanResponseModel
from agent.models.heartbeat import HeartbeatResponseModel

logger = logging.getLogger(__name__)


class ControlPlaneClient(BaseAPIClient):
    """
    Async client for interacting with the Fault Control Plane API.

    Provides methods for:
    - Registering the agent
    - Sending periodic heartbeat signals
    - Fetching fault plans
    - Acknowledging executed plans
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

    async def fetch_plan(self) -> FaultPlanResponseModel:
        """
        Fetch the next fault plan from the control plane.

        Returns:
            Dict[str, Any]: Fault plan details, or an empty plan if none available.
        """
        logger.debug("Fetching fault plan from control plane")
        response: Dict = await self.request("GET", "/api/v1/agent/plan")
        return FaultPlanResponseModel(**response)

    async def ack_plan(self, plan_id: int) -> None:
        """Acknowledge that a fault plan has been received."""
        logger.info("Acknowledging plan with ID: %d", plan_id)
        await self.request("POST", "/api/v1/agent/plan/ack", json={"id": plan_id})
        return
