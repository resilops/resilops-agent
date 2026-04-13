import asyncio
import logging
from typing import Any, Dict, Optional

from agent.clients.control_plane import ControlPlaneClient
from agent.core.worker import PeriodicWorker
from agent.handlers.state import AgentStateHandler
from agent.handlers.telemetry import AgentTelemetry
from agent.schemas.config import AgentConfigModel

logger = logging.getLogger(__name__)


class HealthMonitorWorker(PeriodicWorker):
    """Send periodic heartbeats and reflect the result in agent health state."""

    WORKER_NAME: str = "health_monitor"
    SKIP_HEALTH_CHECK: bool = True

    def __init__(
        self,
        config: AgentConfigModel,
        state_handler: AgentStateHandler,
        telemetry: AgentTelemetry,
        shutdown_event: asyncio.Event,
        client: ControlPlaneClient,
    ):
        """Create the heartbeat worker."""
        super().__init__(config, state_handler, telemetry, shutdown_event)
        self.client = client

    def execution_interval(self) -> int:
        """Return the configured heartbeat interval in seconds."""
        return self.config.heartbeat_interval

    async def run_iteration(self) -> Optional[Dict[str, Any]]:
        """Send one heartbeat request to the control plane."""
        await self.client.send_heartbeat()
        return None

    async def handle_iteration_success(self, context: Dict[str, Any]) -> None:
        """Mark the agent healthy after a successful heartbeat."""
        self.state_handler.agent.set_health(healthy=True)

    async def handle_iteration_error(
        self, context: Dict[str, Any], error: Exception
    ) -> None:
        """Mark the agent unhealthy and log the heartbeat failure."""
        logger.error("Health report request failed", exc_info=error)
        self.state_handler.agent.set_health(healthy=False)
