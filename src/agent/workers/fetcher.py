import asyncio
import logging
from typing import Any, Dict, Optional

from agent.clients.control_plane import ControlPlaneClient
from agent.models.agent import AgentStateModel
from agent.models.config import AgentConfigModel
from agent.models.fault import FaultPlanResponseModel
from agent.workers.base import PeriodicWorker

logger = logging.getLogger(__name__)


class PlanFetcherWorker(PeriodicWorker):
    """
    Periodic worker that polls the control plane for new fault plans.

    Fetches available fault plans and enqueues them for execution.
    Runs at a fixed interval defined in the agent configuration.
    """

    WORKER_NAME: str = "plan_poller"

    def __init__(
        self,
        config: AgentConfigModel,
        agent: AgentStateModel,
        shutdown_event: asyncio.Event,
        client: ControlPlaneClient,
    ):
        """
        Initialize the fault plan fetching worker.

        Args:
            config: Agent configuration containing polling interval.
            agent: Agent model used to access the execution queue.
            shutdown_event: Async event used to gracefully stop the worker loop.
            client: API client used to fetch and acknowledge fault plans.
        """
        super().__init__(config, agent, shutdown_event)
        self.client = client

    @property
    def execution_interval(self) -> int:
        """
        Interval (in seconds) at which fault plans are polled.

        Returns:
            The polling interval defined in the agent configuration.
        """
        return self.config.fault_plan_poll_interval

    async def should_execute(self) -> bool:
        """
        Check if the worker is allowed to run at the current moment.

        Returns:
            bool: True if the worker can run, False if it should be skipped.
        """
        return self.agent.healthy and self.agent.runner.available

    async def execute_iteration(self) -> Optional[Dict[str, FaultPlanResponseModel]]:
        """
        Execute a single polling iteration.
        Fetches a fault plan from the control plane and acknowledges it.
        Returns a context dictionary containing the plan for the success hook.

        Returns:
            A dictionary containing the fetched plan, or None if no plan is available.
        """
        # Fetch new plan and acknowledge
        plan: FaultPlanResponseModel = await self.client.fetch_plan()

        # Acknowledge plan if available
        if plan.available:
            await self.client.ack_plan(plan.id)

        return {"plan": plan}

    async def on_execution_success(self, context: Dict[str, Any]) -> None:
        """
        Handle a successful polling iteration.
        Enqueues the fetched fault plan for execution and logs debug information.

        Args:
            context: Context dictionary returned by `execute_iteration`,
                     containing the plan.
        """
        plan: FaultPlanResponseModel = context.get("plan")
        if not plan.available:
            return

        logger.info("Enqueued new fault plan with id: %s", plan.id)
        self.agent.runner.enqueue(plan)

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
        logger.error("Failed to fetch new fault plan", exc_info=error)
