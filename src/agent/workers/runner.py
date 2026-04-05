import asyncio
import logging
from typing import Any, Dict, Optional

from agent.core.worker import PeriodicWorker
from agent.handlers.runner import ResiliencySuiteRunner
from agent.handlers.state import AgentStateHandler
from agent.handlers.telemetry import AgentTelemetry
from agent.schemas.config import AgentConfigModel
from agent.schemas.event import EventEnum, EventPayload
from agent.schemas.suite import ResiliencySuite

logger = logging.getLogger(__name__)


class ResiliencySuiteRunnerWorker(PeriodicWorker):
    """
    Periodic worker that executes queued resilience test suites.

    Monitors the agent's execution queue and executes the next queued suite, if any.
    Each iteration picks the next suite and runs it. After execution, the executor
    can be reset depending on the context returned by `execute_iteration`.
    """

    WORKER_NAME: str = "suite_executor"

    def __init__(
        self,
        config: AgentConfigModel,
        state_handler: AgentStateHandler,
        telemetry: AgentTelemetry,
        runner: ResiliencySuiteRunner,
        shutdown_event: asyncio.Event,
    ):
        """
        Initialize the resiliency suite executor worker.

        Args:
            config: Agent configuration containing the executor interval.
            state_handler: Internal state handler.
            telemetry: Telemetry handler.
            runner: Resiliency suite runner.
            shutdown_event: Async event used to gracefully stop the worker loop.
        """
        super().__init__(config, state_handler, telemetry, shutdown_event)
        self.runner = runner

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
        Execute the next queued resiliency suite, if available.

        Returns:
            A context dictionary containing:
                - 'suite': The executed suite object, or None if no suite was queued.
        """
        suite: ResiliencySuite = self.state_handler.runner.current_suite
        self.state_handler.runner.mark_running()
        self.telemetry.emit_event(
            event=EventPayload(event_name=EventEnum.SUITE_EXECUTING),
            suite_id=suite.id,
            run_id=suite.run_id,
        )
        await self.runner.run(suite)
        return {"suite": suite}

    async def on_execution_success(self, context: Dict[str, Any]) -> None:
        """
        Handle successful execution of a resiliency suite.

        Resets the executor state if a suite was executed and logs a success message.

        Args:
            context: Context dictionary returned by `execute_iteration`,
                     may contain 'suite'.
        """
        suite: ResiliencySuite = context.get("suite")
        self.state_handler.runner.mark_idle()
        self.telemetry.emit_event(
            event=EventPayload(event_name=EventEnum.SUITE_EXECUTION_SUCCESS),
            suite_id=suite.id,
            run_id=suite.run_id,
        )

    async def on_execution_error(
        self, context: Dict[str, Any], error: Exception
    ) -> None:
        """
        Handle failure during resiliency suite execution.

        Resets the executor state and logs the error.

        Args:
            context: Context dictionary returned by `execute_iteration`,
                     may contain 'suite'.
            error: Exception raised during suite execution.
        """
        # Any error raised should have the context with suite and message
        suite: ResiliencySuite = context.get("suite")

        self.state_handler.runner.mark_idle()
        self.telemetry.emit_event(
            event=EventPayload(
                event_name=EventEnum.SUITE_EXECUTION_FAILED,
                error=error.__class__.__name__,
                data=context,
            ),
            suite_id=suite.id,
            run_id=suite.run_id,
            scenario_id=context.get("scenario_id"),
        )
