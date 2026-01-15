import asyncio
from typing import List, Optional

from agent.schemas.state import (
    AgentHealthStatusEnum,
    AgentRuntimeState,
    ResiliencySuiteLifecycleStateEnum,
    ResiliencySuiteRuntimeState,
)
from agent.schemas.suite import ResiliencySuite


class ResiliencySuiteRuntimeStateHandler:
    """Manages lifecycle transitions for a resiliency suite execution."""

    def __init__(self, state: ResiliencySuiteRuntimeState):
        self._state = state

    @property
    def current_suite(self) -> Optional[ResiliencySuite]:
        return self._state.suite

    @property
    def is_idle(self) -> bool:
        return self._state.state == ResiliencySuiteLifecycleStateEnum.IDLE

    @property
    def is_queued(self) -> bool:
        return self._state.state == ResiliencySuiteLifecycleStateEnum.QUEUED

    def enqueue(self, suite: ResiliencySuite) -> None:
        if not self.is_idle:
            raise RuntimeError("Suite execution slot is busy.")

        self._state.suite = suite
        self._state.state = ResiliencySuiteLifecycleStateEnum.QUEUED

    def mark_running(self) -> None:
        if not self.is_queued:
            raise RuntimeError("Cannot start execution: no suite queued.")

        self._state.state = ResiliencySuiteLifecycleStateEnum.RUNNING

    def mark_idle(self) -> None:
        self._state.suite = None
        self._state.state = ResiliencySuiteLifecycleStateEnum.IDLE


class AgentRuntimeStateHandler:
    """Manages agent-level runtime state."""

    def __init__(self, agent: AgentRuntimeState):
        self._agent = agent

    @property
    def is_healthy(self) -> bool:
        return self._agent.health == AgentHealthStatusEnum.HEALTHY

    @property
    def current_workers(self) -> List[asyncio.Task]:
        """Return currently registered background worker tasks."""
        return self._agent.running_workers

    def register_workers(self, workers: List[asyncio.Task]) -> None:
        """Register active background worker tasks."""
        self._agent.running_workers = workers

    def set_health(self, healthy: bool) -> None:
        """Update agent health status."""
        self._agent.health = (
            AgentHealthStatusEnum.HEALTHY
            if healthy
            else AgentHealthStatusEnum.UNHEALTHY
        )


class AgentStateHandler:
    """
    Facade for all agent state mutations.

    Workers should interact ONLY with this handler.
    """

    def __init__(self) -> None:
        state = AgentRuntimeState()

        self.agent = AgentRuntimeStateHandler(state)
        self.runner = ResiliencySuiteRuntimeStateHandler(state.runner)
