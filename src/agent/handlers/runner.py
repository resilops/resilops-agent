import logging

from reslib.runtime.scenario import execute_resilience_scenario

from agent.clients.control_plane import ControlPlaneClient
from agent.handlers.telemetry import AgentTelemetry, RunTelemetry
from agent.schemas.scenario import ScenarioClaim, ScenarioRun

logger = logging.getLogger(__name__)


class ScenarioRunner:
    """Executes resiliency scenarios and emits execution events."""

    def __init__(self, client: ControlPlaneClient, telemetry: AgentTelemetry):
        self.client = client
        self.telemetry = telemetry

    async def execute_claim(self, claim: ScenarioClaim) -> None:
        """Fetch and execute the scenario referenced by a queued claim."""
        try:
            scenario_run: ScenarioRun = await self.client.fetch_scenario_run(
                scenario_id=claim.scenario_id, run_id=claim.run_id
            )
            await execute_resilience_scenario(
                scenario=scenario_run.config,
                telemetry=RunTelemetry(
                    telemetry=self.telemetry,
                    run_id=scenario_run.id,
                ),
            )
        except Exception as exc:
            logger.exception("Scenario execution failed")
            setattr(exc, "result", {"claim": claim})
            raise
