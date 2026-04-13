import asyncio
from typing import List, Optional

from agent.schemas.scenario import ResiliencyScenarioClaim
from agent.schemas.state import (
    AgentHealthStatusEnum,
    AgentRuntimeState,
    RunnerLifecycleStateEnum,
    RunnerRuntimeState,
)


class RunnerRuntimeStateHandler:
    """Manages lifecycle transitions for a resiliency scenario execution."""

    def __init__(self, state: RunnerRuntimeState):
        self._state = state

    @property
    def current_claim(self) -> Optional[ResiliencyScenarioClaim]:
        """Return the claim currently assigned to the runner, if any."""
        return self._state.claim

    @property
    def is_idle(self) -> bool:
        """Return whether the runner is currently idle."""
        return self._state.state == RunnerLifecycleStateEnum.IDLE

    @property
    def is_queued(self) -> bool:
        """Return whether a claim is queued for execution."""
        return self._state.state == RunnerLifecycleStateEnum.QUEUED

    def enqueue(self, claim: ResiliencyScenarioClaim) -> None:
        """Queue a claim for execution when the runner is idle."""
        if not self.is_idle:
            raise RuntimeError("Scenario claim execution slot is busy.")

        self._state.claim = claim
        self._state.state = RunnerLifecycleStateEnum.QUEUED

    def mark_running(self) -> None:
        """Transition the runner from queued to running."""
        if not self.is_queued:
            raise RuntimeError("Cannot start execution: no claim queued.")

        self._state.state = RunnerLifecycleStateEnum.RUNNING

    def reset_to_idle(self) -> None:
        """Clear the current claim and reset the runner to idle."""
        self._state.claim = None
        self._state.state = RunnerLifecycleStateEnum.IDLE


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
    """Facade exposing the mutable runtime state used by workers."""

    def __init__(self) -> None:
        state = AgentRuntimeState()
        self.agent = AgentRuntimeStateHandler(state)
        self.runner = RunnerRuntimeStateHandler(state.runner)
