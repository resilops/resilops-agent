import logging

from reslib.runtime.scenario import execute_resilience_scenario
from reslib.schemas.scenario import ResiliencyScenario

from agent.clients.control_plane import ControlPlaneClient
from agent.exceptions import ResiliencySuiteExecutionError
from agent.handlers.telemetry import AgentTelemetry, ResLibTelemetryWithContext
from agent.schemas.suite import ResiliencySuite

logger = logging.getLogger(__name__)


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
        telemetry: AgentTelemetry,
    ) -> None:
        self.client = client
        self.telemetry = telemetry

    async def run(self, suite: ResiliencySuite) -> None:
        """
        Execute all scenarios in a suite sequentially.

        Raises:
            ResiliencySuiteExecutionError: if scenario execution or fetching fails.
        """
        for scenario_id in suite.scenarios:
            try:
                scenario = await self.client.fetch_scenario(
                    suite_id=suite.id,
                    scenario_id=scenario_id,
                )
                await execute_resilience_scenario(
                    scenario=ResiliencyScenario(
                        template=scenario.template,
                        steps=[s.model_dump() for s in scenario.steps],
                        observer=scenario.observer.model_dump(),
                    ),
                    telemetry=ResLibTelemetryWithContext(
                        telemetry=AgentTelemetry(),
                        run_id=suite.run_id,
                        suite_id=suite.id,
                        scenario_id=scenario_id,
                    ),
                )
            except Exception as exc:
                raise ResiliencySuiteExecutionError(
                    "Suite execution failed",
                    context={
                        "suite": suite,
                        "error": str(exc),
                        "scenario_id": scenario_id,
                    },
                ) from exc
