import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from agent.handlers.state import AgentStateHandler
from agent.handlers.telemetry import AgentTelemetry
from agent.schemas.config import AgentConfigModel


class BaseWorker(ABC):
    """Abstract base class for all background workers."""

    @property
    @abstractmethod
    def execution_interval(self) -> int:
        """Interval between worker executions in seconds."""

    @abstractmethod
    async def should_execute(self) -> bool:
        """Check if worker should run in current state."""

    @abstractmethod
    async def execute_iteration(self) -> Optional[Dict[str, Any]]:
        """
        Execute one worker iteration.
        Returns optional context data for hooks.
        """

    @abstractmethod
    async def on_execution_success(self, context: Dict[str, Any]) -> None:
        """Called after successful execution."""

    @abstractmethod
    async def on_execution_error(
        self, context: Dict[str, Any], error: Exception
    ) -> None:
        """Called when execution fails."""

    @abstractmethod
    async def run_continuously(self) -> None:
        """Run the worker's main loop until stopped."""


class PeriodicWorker(BaseWorker):
    """Concrete implementation of a periodic background worker."""

    WORKER_NAME: str = "base_worker"

    def __init__(
        self,
        config: AgentConfigModel,
        state_handler: AgentStateHandler,
        telemetry: AgentTelemetry,
        shutdown_event: asyncio.Event,
    ):
        self.config = config
        self.state_handler = state_handler
        self.telemetry = telemetry
        self.shutdown_event = shutdown_event

    async def _execute_safely(self) -> None:
        """Execute one iteration with proper error handling."""
        try:
            context = await self.execute_iteration() or {}
            await self.on_execution_success(context)
        except Exception as error:
            context = getattr(error, "context", {})
            await self.on_execution_error(context, error)

    async def should_execute(self) -> bool:
        """Default precondition: always execute unless overridden."""
        return True

    async def run_continuously(self) -> None:
        """Main execution loop for the periodic worker."""
        while not self.shutdown_event.is_set():
            await asyncio.sleep(self.execution_interval)
            if await self.should_execute():
                await self._execute_safely()
