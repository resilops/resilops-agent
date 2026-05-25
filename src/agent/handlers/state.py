import asyncio
from typing import List, Optional

from agent.schemas.scenario import ScenarioClaimSet
from agent.schemas.state import (
    AgentHealthState,
    AgentState,
    RunnerState,
    RunnerStatus,
)


class RunnerStateHandler:
    """Manages lifecycle transitions for resiliency scenario claim sets."""

    def __init__(self, state: RunnerState):
        self._state = state

    @property
    def current_claim_set(self) -> Optional[ScenarioClaimSet]:
        """Return the claim set currently assigned to the runner, if any."""
        return self._state.claim_set

    @property
    def is_idle(self) -> bool:
        """Return whether the runner is currently idle."""
        return self._state.state == RunnerStatus.IDLE

    @property
    def is_queued(self) -> bool:
        """Return whether a claim set is queued for execution."""
        return self._state.state == RunnerStatus.QUEUED

    def enqueue(self, claim_set: ScenarioClaimSet) -> None:
        """Queue a claim set for execution when the runner is idle."""
        if not self.is_idle:
            raise RuntimeError("Scenario claim set execution slot is busy.")

        self._state.claim_set = claim_set
        self._state.state = RunnerStatus.QUEUED

    def mark_running(self) -> None:
        """Transition the runner from queued to running."""
        if not self.is_queued:
            raise RuntimeError("Cannot start execution: no claim set queued.")

        self._state.state = RunnerStatus.RUNNING

    def reset_to_idle(self) -> None:
        """Clear the current claim set and reset the runner to idle."""
        self._state.claim_set = None
        self._state.state = RunnerStatus.IDLE


class AgentStateView:
    """Manages agent-level runtime state."""

    def __init__(self, agent: AgentState):
        self._agent = agent

    @property
    def is_healthy(self) -> bool:
        return self._agent.health == AgentHealthState.HEALTHY

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
            AgentHealthState.HEALTHY if healthy else AgentHealthState.UNHEALTHY
        )


class AgentStateHandler:
    """Facade exposing the mutable runtime state used by workers."""

    def __init__(self) -> None:
        state = AgentState()
        self.agent = AgentStateView(state)
        self.runner = RunnerStateHandler(state.runner)
