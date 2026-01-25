import logging

from reslib.helpers import BaseEventRecorder
from reslib.runtime.scenario import execute_resilience_scenario
from reslib.schemas.event import ResLibAgentEventPayload

from agent.clients.control_plane import ControlPlaneClient
from agent.exceptions import ResiliencySuiteExecutionError
from agent.handlers.event import EventHandler
from agent.schemas.suite import ResiliencySuite

logger = logging.getLogger(__name__)


class ResLibEventRecorder(BaseEventRecorder):
    """Bridges reslib events to the agent event handler."""

    def __init__(
        self,
        suite: ResiliencySuite,
        scenario_id: int,
        event_handler: EventHandler,
    ) -> None:
        self.suite = suite
        self.scenario_id = scenario_id
        self.event_handler = event_handler

    def record(self, *, event: ResLibAgentEventPayload) -> None:
        """Forward library events to the agent event handler."""
        event.suite_id = self.suite.id
        event.run_id = self.suite.run_id
        event.scenario_id = self.scenario_id
        self.event_handler.publish(event=event)


class ResiliencySuiteRunner:
    """
    Executes resiliency scenarios sequentially and emits execution events.

    Responsibilities:
        - Fetch scenarios from the control plane
        - Execute scenarios as a one-shot suite
        - Surface execution failures with context
    """

    def __init__(
        self,
        client: ControlPlaneClient,
        event_handler: EventHandler,
    ) -> None:
        self.client = client
        self.event_handler = event_handler

    async def run(self, suite: ResiliencySuite) -> None:
        """
        Execute all scenarios in a suite sequentially.

        Raises:
            ResiliencySuiteExecutionError: if scenario execution or fetching fails.
        """
        try:
            for scenario_id in suite.scenarios:
                scenario = await self.client.fetch_scenario(
                    suite_id=suite.id,
                    scenario_id=scenario_id,
                )

                await execute_resilience_scenario(
                    action=scenario.action.model_dump(),
                    observer=scenario.observer.model_dump(),
                    guardrail=scenario.guardrail.model_dump(),
                    rollback=scenario.rollback.model_dump(),
                    event_recorder=ResLibEventRecorder(
                        suite=suite,
                        scenario_id=scenario.id,
                        event_handler=self.event_handler,
                    ),
                )

        except Exception as exc:
            raise ResiliencySuiteExecutionError(
                "Suite execution failed",
                context={"suite_id": suite.id, "error": str(exc)},
            ) from exc
