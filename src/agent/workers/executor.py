import asyncio
import logging
from typing import Any, Dict, Optional

from agent.handlers.event import EventHandler
from agent.handlers.fault import FaultPlanExecutionHandler
from agent.handlers.state import StateHandler
from agent.models.config import AgentConfigModel
from agent.models.event import AgentEventEnum
from agent.models.fault import FaultPlanModel
from agent.workers.base import PeriodicWorker

logger = logging.getLogger(__name__)


class FaultPlanExecutorWorker(PeriodicWorker):
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
        state: StateHandler,
        event: EventHandler,
        executor: FaultPlanExecutionHandler,
        shutdown_event: asyncio.Event,
    ):
        """
        Initialize the fault plan executor worker.

        Args:
            config: Agent configuration containing the executor interval.
            state: Internal state handler.
            event: Event handler.
            executor: Fault plan execution handler.
            shutdown_event: Async event used to gracefully stop the worker loop.
        """
        super().__init__(config, state, event, shutdown_event)
        self.executor = executor

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
        return self.state.agent.is_healthy and self.state.executor.is_queued

    async def execute_iteration(self) -> Optional[Dict[str, Any]]:
        """
        Execute the next queued fault plan, if available.

        Returns:
            A context dictionary containing:
                - 'plan': The executed plan object, or None if no plan was queued.
        """
        plan: FaultPlanModel = self.state.executor.current_plan
        self.state.executor.mark_executing()
        self.event.push(
            AgentEventEnum.PLAN_EXECUTING,
            {"plan_id": plan.id, "run_id": plan.run_id, "details": "Plan executing"},
        )
        await self.executor.run_plan(plan)
        return {"plan": plan}

    async def on_execution_success(self, context: Dict[str, Any]) -> None:
        """
        Handle successful execution of a fault plan.

        Resets the executor state if a plan was executed and logs a success message.

        Args:
            context: Context dictionary returned by `execute_iteration`,
                     may contain 'plan'.
        """
        plan: FaultPlanModel = context.get("plan")
        self.state.executor.reset()
        self.event.push(
            AgentEventEnum.PLAN_EXECUTION_SUCCESS,
            {
                "plan_id": plan.id,
                "run_id": plan.run_id,
                "details": "Plan executed successfully.",
            },
        )

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
        # Any error raised should have the context with plan and failures
        plan, failures = context.get("plan"), context.get("failures")
        self.state.executor.reset()

        for failure in failures:
            self.event.push(
                AgentEventEnum.FAULT_EXECUTION_ERROR,
                {
                    "plan_id": plan.id,
                    "run_id": plan.run_id,
                    "fault_id": failure.get("fault_id"),
                    "details": failure.get("message"),
                },
            )

        self.event.push(
            AgentEventEnum.PLAN_EXECUTION_FAILED,
            {
                "plan_id": plan.id,
                "run_id": plan.run_id,
                "details": (
                    f"Fault execution or API failed. "
                    f"See '{AgentEventEnum.FAULT_EXECUTION_ERROR.value}' event."
                ),
            },
        )
