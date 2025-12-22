import asyncio
import logging
from typing import Any, Dict, Optional

from agent.models.agent import AgentStateModel
from agent.models.config import AgentConfigModel
from agent.models.fault import FaultPlanResponseModel
from agent.workers.base import PeriodicWorker

logger = logging.getLogger(__name__)


class PlanExecutorWorker(PeriodicWorker):
    """
    Periodic worker that executes queued fault plans.

    Monitors the agent's execution queue and executes the next queued plan, if any.
    Each iteration picks the next plan and runs it. After execution, the executor
    can be reset depending on the context returned by `execute_iteration`.
    """

    WORKER_NAME: str = "plan_executor"

    def __init__(
        self,
        config: AgentConfigModel,
        agent: AgentStateModel,
        shutdown_event: asyncio.Event,
    ):
        """
        Initialize the fault plan executor worker.

        Args:
            config: Agent configuration containing the executor interval.
            agent: Agent model containing the execution queue.
            shutdown_event: Async event used to gracefully stop the worker loop.
        """
        super().__init__(config, agent, shutdown_event)

    @property
    def execution_interval(self) -> int:
        """
        Interval (in seconds) at which the executor checks the queue.

        Returns:
            Executor interval defined in the agent configuration.
        """
        return self.config.runner_interval

    async def should_execute(self) -> bool:
        """
        Check if the worker is allowed to run at the current moment.

        Returns:
            bool: True if the worker can run, False if it should be skipped.
        """
        return self.agent.healthy and self.agent.runner.queued

    async def execute_iteration(self) -> Optional[Dict[str, Any]]:
        """
        Execute the next queued fault plan, if available.

        Returns:
            A context dictionary containing:
                - 'plan': The executed plan object, or None if no plan was queued.
        """
        plan: FaultPlanResponseModel = self.agent.runner.plan
        await plan.execute()
        return {"plan": plan}

    async def on_execution_success(self, context: Dict[str, Any]) -> None:
        """
        Handle successful execution of a fault plan.

        Resets the executor state if a plan was executed and logs a success message.

        Args:
            context: Context dictionary returned by `execute_iteration`,
                     may contain 'plan'.
        """
        plan: FaultPlanResponseModel = context.get("plan")
        logger.info("Fault plan with id: %s executed successfully.", plan.id)
        self.agent.runner.reset()

    async def on_execution_error(
        self, context: Dict[str, Any], error: Exception
    ) -> None:
        """
        Handle failure during fault plan execution.

        Resets the executor state and logs the error.

        Args:
            context: Context dictionary returned by `execute_iteration`,
                     may contain 'plan'.
            error: Exception raised during plan execution.
        """
        logger.info("Fault plan execution failed", exc_info=error)
        self.agent.runner.reset()
