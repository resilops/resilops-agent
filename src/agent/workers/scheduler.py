import asyncio
import logging
from typing import Any, Dict, Optional

from agent.clients.control_plane import ControlPlaneClient
from agent.core.worker import PeriodicWorker
from agent.exceptions import APIRequestError
from agent.handlers.state import AgentStateHandler
from agent.handlers.telemetry import AgentTelemetry
from agent.schemas.config import AgentConfig
from agent.schemas.event import EventEnum, EventPayload
from agent.schemas.scenario import ScenarioClaimSet

logger = logging.getLogger(__name__)


class ScenarioSchedulerWorker(PeriodicWorker):
    """Poll the control plane for scenario claim sets and queue them locally."""

    WORKER_NAME: str = "scenario_scheduler"

    def __init__(
        self,
        config: AgentConfig,
        state_handler: AgentStateHandler,
        telemetry: AgentTelemetry,
        shutdown_event: asyncio.Event,
        client: ControlPlaneClient,
    ) -> None:
        """Create the scenario scheduler worker."""
        super().__init__(config, state_handler, telemetry, shutdown_event)
        self.client = client

    def execution_interval(self) -> int:
        """
        Interval (in seconds) at which the control plane is polled.

        Returns:
            Polling interval defined in the agent configuration.
        """
        return self.config.resiliency_scenario_poll_interval

    async def should_execute(self) -> bool:
        """Poll only when the agent is healthy and the runner is idle."""
        return self.state_handler.agent.is_healthy and self.state_handler.runner.is_idle

    async def run_iteration(self) -> Optional[Dict[str, ScenarioClaimSet]]:
        """Fetch and acknowledge the next claim set, if one is available."""
        logger.info("Checking if there are any new claim sets")
        claim_set: Optional[ScenarioClaimSet] = (
            await self.client.fetch_scenario_claim_set()
        )
        if claim_set:
            await self.client.ack_scenario_claim_set(claim_set.id)

        return {"claim_set": claim_set}

    async def handle_iteration_success(self, result: Dict[str, Any]) -> None:
        """Queue the fetched claim set and emit queued events."""
        claim_set: Optional[ScenarioClaimSet] = result.get("claim_set")
        if not claim_set:
            return

        self.state_handler.runner.enqueue(claim_set)
        for claim in claim_set.claims:
            self.telemetry.emit_event(
                event=EventPayload(event_name=EventEnum.SCENARIO_QUEUED),
                run_id=claim.run_id,
            )

    async def handle_iteration_error(
        self, result: Dict[str, Any], error: Exception
    ) -> None:
        """Handle polling errors without enqueueing a claim set."""
        if isinstance(error, APIRequestError):
            error.status_code = 409
            logger.debug("Some other agent acknowledged the claim set first")
            return

        logger.error(
            "Failed to poll/acknowledge resiliency scenario claim set",
            exc_info=error,
        )
