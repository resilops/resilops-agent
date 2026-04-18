import asyncio
import logging
from typing import Any, Dict, Optional

from agent.core.worker import PeriodicWorker
from agent.handlers.runner import ScenarioRunner
from agent.handlers.state import AgentStateHandler
from agent.handlers.telemetry import AgentTelemetry
from agent.schemas.config import AgentConfig
from agent.schemas.event import EventEnum, EventPayload
from agent.schemas.scenario import ScenarioClaim

logger = logging.getLogger(__name__)


class ScenarioRunnerWorker(PeriodicWorker):
    """Execute queued scenario claims when the agent is healthy."""

    WORKER_NAME: str = "scenario_executor"

    def __init__(
        self,
        config: AgentConfig,
        state_handler: AgentStateHandler,
        telemetry: AgentTelemetry,
        runner: ScenarioRunner,
        shutdown_event: asyncio.Event,
    ):
        """Create the scenario runner worker."""
        super().__init__(config, state_handler, telemetry, shutdown_event)
        self.runner = runner

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
            scenario_id=claim.scenario_id,
            run_id=claim.run_id,
        )

    def execution_interval(self) -> int:
        """
        Interval (in seconds) at which the executor checks the queue.

        Returns:
            Executor interval defined in the agent configuration.
        """
        return self.config.runner_interval

    async def should_execute(self) -> bool:
        """Run only when the agent is healthy and a claim is queued."""
        return (
            self.state_handler.agent.is_healthy and self.state_handler.runner.is_queued
        )

    async def run_iteration(self) -> Optional[Dict[str, Any]]:
        """Execute the queued claim and return it as iteration context."""
        claim: ScenarioClaim = self.state_handler.runner.current_claim
        self.state_handler.runner.mark_running()
        self._emit_claim_event(EventEnum.SCENARIO_EXECUTING, claim)
        await self.runner.execute_claim(claim)
        return {"claim": claim}

    async def handle_iteration_success(self, result: Dict[str, Any]) -> None:
        """Reset runner state and emit a success event for the claim."""
        claim: ScenarioClaim = result.get("claim")
        self.state_handler.runner.reset_to_idle()
        self._emit_claim_event(EventEnum.SCENARIO_EXECUTION_SUCCESS, claim)

    async def handle_iteration_error(
        self, result: Dict[str, Any], error: Exception
    ) -> None:
        """Reset runner state and emit a failure event for the claim."""
        claim: ScenarioClaim = result.get("claim")

        self.state_handler.runner.reset_to_idle()
        self._emit_claim_event(
            EventEnum.SCENARIO_EXECUTION_FAILED,
            claim,
            data=result,
            error=error.__class__.__name__,
        )
