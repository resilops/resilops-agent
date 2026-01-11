import asyncio
import logging
from typing import Any, Dict, Optional

from agent.core.worker import PeriodicWorker
from agent.handlers.event import EventHandler
from agent.handlers.runner import ResiliencyPlanRunner
from agent.handlers.state import AgentStateHandler
from agent.schemas.config import AgentConfigModel
from agent.schemas.event import AgentEventEnum
from agent.schemas.resiliency import ResiliencyPlan

logger = logging.getLogger(__name__)


class ResiliencyPlanRunnerWorker(PeriodicWorker):
    """
    Periodic worker that executes queued resilience test plans.

    Monitors the agent's execution queue and executes the next queued plan, if any.
    Each iteration picks the next plan and runs it. After execution, the executor
    can be reset depending on the context returned by `execute_iteration`.
    """

    WORKER_NAME: str = "plan_executor"

    def __init__(
        self,
        config: AgentConfigModel,
        state_handler: AgentStateHandler,
        event_handler: EventHandler,
        runner: ResiliencyPlanRunner,
        shutdown_event: asyncio.Event,
    ):
        """
        Initialize the resiliency plan executor worker.

        Args:
            config: Agent configuration containing the executor interval.
            state_handler: Internal state handler.
            event_handler: Event handler.
            runner: Resiliency plan runner.
            shutdown_event: Async event used to gracefully stop the worker loop.
        """
        super().__init__(config, state_handler, event_handler, shutdown_event)
        self.runner = runner

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
        return (
            self.state_handler.agent.is_healthy and self.state_handler.runner.is_queued
        )

    async def execute_iteration(self) -> Optional[Dict[str, Any]]:
        """
        Execute the next queued resiliency plan, if available.

        Returns:
            A context dictionary containing:
                - 'plan': The executed plan object, or None if no plan was queued.
        """
        plan: ResiliencyPlan = self.state_handler.runner.current_plan
        self.state_handler.runner.mark_running()
        self.event_handler.publish(
            plan=plan,
            name=AgentEventEnum.PLAN_EXECUTING,
            payload={"details": "Plan executing"},
        )
        await self.runner.run(plan)
        return {"plan": plan}

    async def on_execution_success(self, context: Dict[str, Any]) -> None:
        """
        Handle successful execution of a resiliency plan.

        Resets the executor state if a plan was executed and logs a success message.

        Args:
            context: Context dictionary returned by `execute_iteration`,
                     may contain 'plan'.
        """
        plan: ResiliencyPlan = context.get("plan")
        self.state_handler.runner.mark_idle()
        self.event_handler.publish(
            plan=plan,
            name=AgentEventEnum.PLAN_EXECUTION_SUCCESS,
            payload={"details": "Plan executed successfully."},
        )

    async def on_execution_error(
        self, context: Dict[str, Any], error: Exception
    ) -> None:
        """
        Handle failure during resiliency plan execution.

        Resets the executor state and logs the error.

        Args:
            context: Context dictionary returned by `execute_iteration`,
                     may contain 'plan'.
            error: Exception raised during plan execution.
        """
        # Any error raised should have the context with plan and message
        plan, err = context.get("plan"), context.get("message")
        self.state_handler.runner.mark_idle()

        self.event_handler.publish(
            plan=plan,
            name=AgentEventEnum.PLAN_EXECUTION_FAILED,
            payload={"details": "Resiliency plan execution failed.", "message": err},
        )
