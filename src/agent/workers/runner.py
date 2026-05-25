import asyncio
import logging
from typing import Any, Dict, Optional

from agent.core.worker import PeriodicWorker
from agent.handlers.runner import ScenarioRunner
from agent.handlers.state import AgentStateHandler
from agent.handlers.telemetry import AgentTelemetry
from agent.schemas.config import AgentConfig
from agent.schemas.scenario import ScenarioClaimSet

logger = logging.getLogger(__name__)


class ScenarioRunnerWorker(PeriodicWorker):
    """Execute queued scenario claim sets when the agent is healthy."""

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

    def execution_interval(self) -> int:
        """
        Interval (in seconds) at which the executor checks the queue.

        Returns:
            Executor interval defined in the agent configuration.
        """
        return self.config.runner_interval

    async def should_execute(self) -> bool:
        """Run only when the agent is healthy and a claim set is queued."""
        return (
            self.state_handler.agent.is_healthy and self.state_handler.runner.is_queued
        )

    async def run_iteration(self) -> Optional[Dict[str, Any]]:
        """Execute the queued claim set."""
        claim_set: ScenarioClaimSet = self.state_handler.runner.current_claim_set
        self.state_handler.runner.mark_running()
        await self.runner.execute_claim_set(claim_set)
        return {"claim_set": claim_set}

    async def handle_iteration_success(self, result: Dict[str, Any]) -> None:
        """Reset runner state after a claim set completes."""
        self.state_handler.runner.reset_to_idle()

    async def handle_iteration_error(
        self, result: Dict[str, Any], error: Exception
    ) -> None:
        """Reset runner state after a claim set failure."""
        self.state_handler.runner.reset_to_idle()
        logger.error("Scenario claim set execution failed", exc_info=error)
