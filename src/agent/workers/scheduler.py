import asyncio
import logging
from typing import Any, Dict, Optional

from agent.clients.control_plane import ControlPlaneClient
from agent.core.worker import PeriodicWorker
from agent.handlers.event import EventHandler
from agent.handlers.state import AgentStateHandler
from agent.schemas.config import AgentConfigModel
from agent.schemas.event import AgentEventEnum
from agent.schemas.suite import ResiliencySuite

logger = logging.getLogger(__name__)


class ResiliencySuiteSchedulerWorker(PeriodicWorker):
    """
    Periodic worker responsible for scheduling resiliency suites.

    Polls the control plane for available resiliency suites, acknowledges
    them, and enqueues eligible suites for execution.
    """

    WORKER_NAME: str = "suite_scheduler"

    def __init__(
        self,
        config: AgentConfigModel,
        state_handler: AgentStateHandler,
        event_handler: EventHandler,
        shutdown_event: asyncio.Event,
        client: ControlPlaneClient,
    ) -> None:
        """
        Initialize the resiliency suite scheduler worker.

        Args:
            config: Agent configuration containing polling interval.
            state_handler: Internal state handler.
            event_handler: Event handler.
            shutdown_event: Async event used to gracefully stop the worker loop.
            client: Control plane API client.
        """
        super().__init__(config, state_handler, event_handler, shutdown_event)
        self.client = client

    @property
    def execution_interval(self) -> int:
        """
        Interval (in seconds) at which the control plane is polled.

        Returns:
            Polling interval defined in the agent configuration.
        """
        return self.config.resiliency_suite_poll_interval

    async def should_execute(self) -> bool:
        """
        Determine whether the scheduler can poll for new suite.

        Returns:
            True if the agent is healthy and ready to enqueue a suite.
        """
        return self.state_handler.agent.is_healthy and self.state_handler.runner.is_idle

    async def execute_iteration(self) -> Optional[Dict[str, ResiliencySuite]]:
        """
        Poll the control plane for a resiliency suite and acknowledge it.

        Returns:
            Context dictionary containing the fetched suite,
            or None if no suite was returned.
        """
        suite: Optional[ResiliencySuite] = await self.client.fetch_suite()

        if suite:
            await self.client.ack_suite(suite.id)

        return {"suite": suite}

    async def on_execution_success(self, context: Dict[str, Any]) -> None:
        """
        Enqueue the fetched resiliency suite for execution.

        Args:
            context: Context dictionary containing the fetched suite.
        """
        suite: Optional[ResiliencySuite] = context.get("suite")

        if not suite:
            return

        self.state_handler.runner.enqueue(suite)
        self.event_handler.publish(
            suite=suite,
            name=AgentEventEnum.SUITE_QUEUED,
            payload={"details": "Resiliency suite queued for execution."},
        )

    async def on_execution_error(
        self, context: Dict[str, Any], error: Exception
    ) -> None:
        """Handle errors during polling without enqueuing any suite."""
        logger.error(
            "Failed to poll resiliency suite from control plane",
            exc_info=error,
        )
