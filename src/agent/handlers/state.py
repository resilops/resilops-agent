import asyncio
from typing import List, Optional, Type

from agent.schemas.resiliency import ResiliencyPlanModel
from agent.schemas.state import (
    AgentStateEnum,
    AgentStateModel,
    ResiliencyPlanExecutionStateEnum,
    ResiliencyPlanExecutionStateModel,
)


class ExecutorStateHandler:
    """Handles state transitions for a resiliency plan execution."""

    def __init__(self, executor: ResiliencyPlanExecutionStateModel):
        self._executor = executor

    @property
    def current_plan(self) -> Optional[ResiliencyPlanModel]:
        """Return the currently assigned resiliency plan, if any."""
        return self._executor.plan

    @property
    def is_available(self) -> bool:
        """Return True if the plan execution slot is available for a new plan."""
        return self._executor.state == ResiliencyPlanExecutionStateEnum.AVAILABLE

    @property
    def is_queued(self) -> bool:
        """Return True if a resiliency plan is queued for execution."""
        return self._executor.state == ResiliencyPlanExecutionStateEnum.QUEUED

    def reset(self) -> None:
        """Clear the queued plan and mark the execution slot as available."""
        self._executor.plan = None
        self._executor.state = ResiliencyPlanExecutionStateEnum.AVAILABLE

    def mark_executing(self) -> None:
        """Mark the plan execution as currently executing."""
        self._executor.state = ResiliencyPlanExecutionStateEnum.EXECUTING

    def enqueue_plan(self, plan: ResiliencyPlanModel) -> bool:
        """
        Queue a resiliency plan for execution if the execution slot is available.

        Args:
            plan: Resiliency plan to queue.

        Returns:
            True if the plan was successfully queued, False otherwise.
        """
        if not self.is_available:
            raise RuntimeError("Runner is busy, cannot queue at the moment.")

        self._executor.plan = plan
        self._executor.state = ResiliencyPlanExecutionStateEnum.QUEUED
        return True


class AgentStateHandler:
    """Handles agent-level state updates triggered by worker outcomes."""

    def __init__(self, agent: AgentStateModel):
        self._agent = agent

    @property
    def is_healthy(self) -> bool:
        """Return true if agent is healthy"""
        return self._agent.status == AgentStateEnum.HEALTHY

    @property
    def current_workers(self) -> List[asyncio.Task]:
        """Return the currently registered background worker tasks."""
        return self._agent.running_workers

    def register_workers(self, workers: List[asyncio.Task]) -> None:
        """Register active background worker tasks."""
        self._agent.running_workers = workers

    def set_health(self, healthy: bool) -> None:
        """Update the agent's health status."""
        self._agent.status = (
            AgentStateEnum.HEALTHY if healthy else AgentStateEnum.UNHEALTHY
        )


class StateHandler:
    """
    Facade for all agent state mutations.

    Workers should interact ONLY with this handler, never directly
    with the underlying state models.
    """

    def __init__(
        self,
        agent_state_handler_cls: Type[AgentStateHandler] = AgentStateHandler,
        executor_state_handler_cls: Type[ExecutorStateHandler] = (ExecutorStateHandler),
    ):
        self._state = AgentStateModel()

        self.agent = agent_state_handler_cls(agent=self._state)
        self.executor = executor_state_handler_cls(executor=self._state.executor)
