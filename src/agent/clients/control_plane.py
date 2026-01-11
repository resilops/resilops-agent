import logging
from typing import Dict

from agent.clients.base import BaseAPIClient
from agent.schemas.heartbeat import HeartbeatResponseModel
from agent.schemas.resiliency import Experiment, ResiliencyPlan

logger = logging.getLogger(__name__)


class ControlPlaneClient(BaseAPIClient):
    """
    Async client for interacting with the Control Plane API.

    Provides methods for:
    - Registering the agent
    - Sending periodic heartbeat signals
    - Fetching resiliency plans
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

    async def fetch_plan(self) -> ResiliencyPlan:
        """
        Fetch the next resiliency plan from the control plane.

        Returns:
            ResiliencyPlan: Resiliency plan details, or an empty plan if
            none available.
        """
        logger.debug("Fetching resiliency plan from control plane")
        response: Dict = await self.request("GET", "/api/v1/agent/plan")
        return ResiliencyPlan(**response)

    async def ack_plan(self, plan_id: int) -> None:
        """Acknowledge that a resiliency plan has been received."""
        logger.info("Acknowledging plan with ID: %d", plan_id)
        await self.request("POST", "/api/v1/agent/plan/ack", json={"id": plan_id})
        return

    async def fetch_experiment(self, plan_id: int, exp_id: int) -> Experiment:
        """
        Fetch the resiliency experiment information given id.

        Returns:
            Experiment: Returns experiment instructions.
        """
        logger.debug("Fetching resiliency experiment from control plane")
        response: Dict = await self.request(
            "GET", f"/api/v1/agent/plan/{plan_id}/experiment/{exp_id}"
        )
        return Experiment(**response)
