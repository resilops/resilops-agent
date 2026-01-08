import asyncio
import logging
from typing import Any, Dict, Optional

from agent.clients.control_plane import ControlPlaneClient
from agent.handlers.event import EventHandler
from agent.handlers.state import StateHandler
from agent.schemas.config import AgentConfigModel
from agent.schemas.event import AgentEventEnum
from agent.schemas.resiliency import ResiliencyPlanModel
from agent.workers.base import PeriodicWorker

logger = logging.getLogger(__name__)


class ResiliencyPlanFetcherWorker(PeriodicWorker):
    """
    Periodic worker that polls the control plane for new resiliency plans.

    Fetches available resiliency plans and enqueues them for execution.
    Runs at a fixed interval defined in the agent configuration.
    """

    WORKER_NAME: str = "plan_poller"

    def __init__(
        self,
        config: AgentConfigModel,
        state: StateHandler,
        event: EventHandler,
        shutdown_event: asyncio.Event,
        client: ControlPlaneClient,
    ):
        """
        Initialize the resiliency plan fetching worker.

        Args:
            config: Agent configuration containing polling interval.
            state: Internal state handler.
            event: Event handler.
            shutdown_event: Async event used to gracefully stop the worker loop.
            client: API client used to fetch and acknowledge resiliency plans.
        """
        super().__init__(config, state, event, shutdown_event)
        self.client = client

    @property
    def execution_interval(self) -> int:
        """
        Interval (in seconds) at which resiliency plans are polled.

        Returns:
            The polling interval defined in the agent configuration.
        """
        return self.config.resiliency_plan_poll_interval

    async def should_execute(self) -> bool:
        """
        Check if the worker is allowed to run at the current moment.

        Returns:
            bool: True if the worker can run, False if it should be skipped.
        """
        return self.state.agent.is_healthy and self.state.executor.is_available

    async def execute_iteration(self) -> Optional[Dict[str, ResiliencyPlanModel]]:
        """
        Execute a single polling iteration.
        Fetches a resiliency plan from the control plane and acknowledges it.
        Returns a context dictionary containing the plan for the success hook.

        Returns:
            A dictionary containing the fetched plan, or None if no plan is available.
        """
        # Fetch new plan and acknowledge
        plan: ResiliencyPlanModel = await self.client.fetch_plan()

        # Acknowledge plan if available
        if plan.available:
            await self.client.ack_plan(plan.id)

        return {"plan": plan}

    async def on_execution_success(self, context: Dict[str, Any]) -> None:
        """
        Handle a successful polling iteration.
        Enqueues the fetched resiliency plan for execution and
        logs debug information.

        Args:
            context: Context dictionary returned by `execute_iteration`,
                     containing the plan.
        """
        plan: ResiliencyPlanModel = context.get("plan")

        # If plan is not available skip enqueue
        if not plan or not plan.available:
            return

        self.state.executor.enqueue_plan(context.get("plan"))
        self.event.push(
            AgentEventEnum.PLAN_QUEUED,
            {"plan_id": plan.id, "run_id": plan.run_id, "details": "Plan queued."},
        )

    async def on_execution_error(
        self, context: Dict[str, Any], error: Exception
    ) -> None:
        """
        Handle errors during polling. Logs the exception without enqueuing any plan.

        Args:
            context: Context dictionary returned by `execute_iteration`
                     (maybe empty or partial).
            error: The exception raised during polling.
        """
        # Note: Do not push event on error!!
        logger.error("Failed to fetch new resiliency plan", exc_info=error)
