import asyncio
import logging
from typing import Any, Dict, Optional

from agent.clients.control_plane import ControlPlaneClient
from agent.core.worker import PeriodicWorker
from agent.handlers.event import EventHandler
from agent.handlers.state import AgentStateHandler
from agent.schemas.config import AgentConfigModel
from agent.schemas.event import AgentEventEnum
from agent.schemas.resiliency import ResiliencyPlan

logger = logging.getLogger(__name__)


class ResiliencyPlanSchedulerWorker(PeriodicWorker):
    """
    Periodic worker responsible for scheduling resiliency plans.

    Polls the control plane for available resiliency plans, acknowledges
    them, and enqueues eligible plans for execution.
    """

    WORKER_NAME: str = "plan_scheduler"

    def __init__(
        self,
        config: AgentConfigModel,
        state_handler: AgentStateHandler,
        event_handler: EventHandler,
        shutdown_event: asyncio.Event,
        client: ControlPlaneClient,
    ) -> None:
        """
        Initialize the resiliency plan scheduler worker.

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
        return self.config.resiliency_plan_poll_interval

    async def should_execute(self) -> bool:
        """
        Determine whether the scheduler can poll for new plans.

        Returns:
            True if the agent is healthy and ready to enqueue a plan.
        """
        return self.state_handler.agent.is_healthy and self.state_handler.runner.is_idle

    async def execute_iteration(self) -> Optional[Dict[str, ResiliencyPlan]]:
        """
        Poll the control plane for a resiliency plan and acknowledge it.

        Returns:
            Context dictionary containing the fetched plan,
            or None if no plan was returned.
        """
        plan: ResiliencyPlan = await self.client.fetch_plan()

        if plan and plan.available:
            await self.client.ack_plan(plan.id)

        return {"plan": plan}

    async def on_execution_success(self, context: Dict[str, Any]) -> None:
        """
        Enqueue the fetched resiliency plan for execution.

        Args:
            context: Context dictionary containing the fetched plan.
        """
        plan: ResiliencyPlan = context.get("plan")

        if not plan or not plan.available:
            return

        self.state_handler.runner.enqueue(plan)
        self.event_handler.publish(
            plan=plan,
            name=AgentEventEnum.PLAN_QUEUED,
            payload={"details": "Resiliency plan queued for execution."},
        )

    async def on_execution_error(
        self, context: Dict[str, Any], error: Exception
    ) -> None:
        """Handle errors during polling without enqueuing any plan."""
        logger.error(
            "Failed to poll resiliency plan from control plane",
            exc_info=error,
        )
