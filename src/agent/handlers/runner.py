import logging

from reslib.runtime.scenario import execute_resilience_scenario

from agent.clients.control_plane import ControlPlaneClient
from agent.handlers.telemetry import AgentTelemetry, AgentTelemetryWithRunContext
from agent.schemas.scenario import ResiliencyScenario, ResiliencyScenarioClaim

logger = logging.getLogger(__name__)


class ResiliencyScenarioRunner:
    """Executes resiliency scenarios and emits execution events."""

    def __init__(self, client: ControlPlaneClient, telemetry: AgentTelemetry):
        self.client = client
        self.telemetry = telemetry

    async def execute_claim(self, claim: ResiliencyScenarioClaim) -> None:
        """Fetch and execute the scenario referenced by a queued claim."""
        try:
            scenario: ResiliencyScenario = await self.client.fetch_scenario(
                scenario_id=claim.scenario_id
            )
            await execute_resilience_scenario(
                scenario=scenario,
                telemetry=AgentTelemetryWithRunContext(
                    telemetry=self.telemetry,
                    run_id=scenario.run_id,
                    scenario_id=scenario.id,
                ),
            )
        except Exception as exc:
            logger.exception("Scenario execution failed")
            setattr(exc, "context", {"claim": claim})
            raise
