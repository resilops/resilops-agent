import logging
import time
from typing import Any, Dict, Optional

from reslib.runtime.scenario import execute_resilience_scenario

from agent.clients.control_plane import ControlPlaneClient
from agent.constants import ScenarioClaimSetExecutionMode
from agent.handlers.telemetry import AgentTelemetry, RunTelemetry
from agent.schemas.event import EventEnum, EventPayload
from agent.schemas.scenario import ScenarioClaim, ScenarioClaimSet, ScenarioRun

logger = logging.getLogger(__name__)


class ScenarioRunner:
    """Executes resiliency scenario claim sets and emits execution events."""

    def __init__(self, client: ControlPlaneClient, telemetry: AgentTelemetry):
        self.client = client
        self.telemetry = telemetry

    def _emit_claim_event(
        self,
        event_name: EventEnum,
        claim: ScenarioClaim,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Emit a telemetry event tied to a specific scenario claim."""
        self.telemetry.emit_event(
            event=EventPayload(event_name=event_name, data=data, error=error),
            run_id=claim.run_id,
        )

    async def execute_claim(self, claim: ScenarioClaim) -> None:
        """Fetch and execute the scenario referenced by a queued claim."""
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

    async def execute_claim_set(self, claim_set: ScenarioClaimSet) -> None:
        """Execute all claims in a claim set by position and execution mode."""
        for claim in sorted(claim_set.claims, key=lambda item: item.position):
            try:
                self._emit_claim_event(EventEnum.SCENARIO_EXECUTING, claim)
                await self.execute_claim(claim)
                self._emit_claim_event(EventEnum.SCENARIO_EXECUTION_SUCCESS, claim)
            except Exception as exc:
                logger.exception("Scenario execution failed")
                result = {"claim_set": claim_set, "claim": claim}
                self._emit_claim_event(
                    EventEnum.SCENARIO_EXECUTION_FAILED,
                    claim,
                    data=result,
                    error=exc.__class__.__name__,
                )
                if (
                    claim_set.execution_mode
                    == ScenarioClaimSetExecutionMode.stop_on_failure
                ):
                    setattr(exc, "result", result)
                    raise

            time.sleep(3)  # Time between runs
