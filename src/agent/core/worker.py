import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from agent.handlers.state import AgentStateHandler
from agent.handlers.telemetry import AgentTelemetry
from agent.schemas.config import AgentConfig


class BaseWorker(ABC):
    """Abstract base class for all background workers."""

    @abstractmethod
    def execution_interval(self) -> int:
        """Interval between worker executions in seconds."""

    @abstractmethod
    async def should_execute(self) -> bool:
        """Check if worker should run in current state."""

    @abstractmethod
    async def run_iteration(self) -> Optional[Dict[str, Any]]:
        """
        Execute one worker iteration.
        Returns optional result data for hooks.
        """

    @abstractmethod
    async def handle_iteration_success(self, result: Dict[str, Any]) -> None:
        """Called after successful execution."""

    @abstractmethod
    async def handle_iteration_error(
        self, result: Dict[str, Any], error: Exception
    ) -> None:
        """Called when execution fails."""

    @abstractmethod
    async def run_continuously(self) -> None:
        """Run the worker's main loop until stopped."""


class PeriodicWorker(BaseWorker):  # noqa
    """Base implementation for workers that run on a fixed interval."""

    WORKER_NAME: str = "base_worker"

    def __init__(
        self,
        config: AgentConfig,
        state_handler: AgentStateHandler,
        telemetry: AgentTelemetry,
        shutdown_event: asyncio.Event,
    ):
        """Store shared dependencies needed by periodic workers."""
        self.config = config
        self.state_handler = state_handler
        self.telemetry = telemetry
        self.shutdown_event = shutdown_event

    async def _execute_safely(self) -> None:
        """Execute one iteration with proper error handling."""
        try:
            result = await self.run_iteration() or {}
            await self.handle_iteration_success(result)
        except Exception as error:
            result = getattr(error, "result", getattr(error, "context", {}))
            await self.handle_iteration_error(result, error)

    async def should_execute(self) -> bool:
        """Default precondition: always execute unless overridden."""
        return True

    async def _sleep_until_next_iteration(self) -> None:
        """Sleep for the configured interval before the next execution cycle."""
        await asyncio.sleep(self.execution_interval())

    async def run_continuously(self) -> None:
        """Run the worker loop until shutdown is requested."""
        while not self.shutdown_event.is_set():
            await self._sleep_until_next_iteration()

            if self.shutdown_event.is_set():
                break

            if await self.should_execute():
                await self._execute_safely()
