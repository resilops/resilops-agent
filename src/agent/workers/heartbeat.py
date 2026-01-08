import asyncio
import logging
from typing import Any, Dict, Optional

from agent.clients.control_plane import ControlPlaneClient
from agent.handlers.event import EventHandler
from agent.handlers.state import StateHandler
from agent.schemas.config import AgentConfigModel
from agent.workers.base import PeriodicWorker

logger = logging.getLogger(__name__)


class HealthMonitorWorker(PeriodicWorker):
    """
    Periodic worker responsible for sending health status to the control plane.

    This worker reports the liveness of the agent at a fixed interval.
    On successful health report delivery, the agent is marked as HEALTHY.
    On failure, the agent is marked as UNHEALTHY.
    """

    WORKER_NAME: str = "health_monitor"
    SKIP_HEALTH_CHECK: bool = True

    def __init__(
        self,
        config: AgentConfigModel,
        state: StateHandler,
        event: EventHandler,
        shutdown_event: asyncio.Event,
        client: ControlPlaneClient,
    ):
        """
        Initialize the health reporter worker.

        Args:
            config: Agent configuration containing health report interval settings.
            state: Internal state handler.
            event: Event handler.
            shutdown_event: Async event used to gracefully stop the worker loop.
            client: API client used to communicate with the control plane.
        """
        super().__init__(config, state, event, shutdown_event)
        self.client = client

    @property
    def execution_interval(self) -> int:
        """
        Interval (in seconds) at which health reports are sent.

        Returns:
            Health report interval defined in the agent configuration.
        """
        return self.config.heartbeat_interval

    async def execute_iteration(self) -> Optional[Dict[str, Any]]:
        """
        Send a single health report to the control plane.
        This method performs the actual health API call.
        Any exception raised here will be handled by the base worker
        and routed to the error hook.

        Returns:
            Optional context dictionary. Not used for health reporting.
        """
        await self.client.send_heartbeat()
        return None

    async def on_execution_success(self, context: Dict[str, Any]) -> None:
        """
        Handle successful health report delivery. Marks the agent as healthy.

        Args:
            context: Context returned by `execute_iteration` (unused).
        """
        self.state.agent.set_health(healthy=True)

    async def on_execution_error(
        self, context: Dict[str, Any], error: Exception
    ) -> None:
        """
        Handle health report failure. Marks the agent as unhealthy and logs the error.

        Args:
            context: Context returned by `execute_iteration` (unused).
            error: Exception raised during health report execution.
        """
        logger.error("Health report request failed: %s", exc_info=error)
        self.state.agent.set_health(healthy=False)
