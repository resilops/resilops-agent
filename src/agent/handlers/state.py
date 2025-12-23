import asyncio
from typing import List, Optional, Type

from agent.models.fault import FaultPlanModel
from agent.models.state import (
    AgentStateEnum,
    AgentStateModel,
    FaultPlanExecutionStateEnum,
    FaultPlanExecutionStateModel,
)


class FaultPlanExecutionHandler:
    """Handles state transitions for a fault plan execution."""

    def __init__(self, executor: FaultPlanExecutionStateModel):
        self._executor = executor

    @property
    def current_plan(self) -> Optional[FaultPlanModel]:
        """Return the currently assigned fault plan, if any."""
        return self._executor.plan

    @property
    def is_available(self) -> bool:
        """Return True if the plan execution slot is available for a new plan."""
        return self._executor.state == FaultPlanExecutionStateEnum.AVAILABLE

    @property
    def is_queued(self) -> bool:
        """Return True if a fault plan is queued for execution."""
        return self._executor.state == FaultPlanExecutionStateEnum.QUEUED

    def reset(self) -> None:
        """Clear the queued plan and mark the execution slot as available."""
        self._executor.plan = None
        self._executor.state = FaultPlanExecutionStateEnum.AVAILABLE

    def mark_executing(self) -> None:
        """Mark the plan execution as currently executing."""
        self._executor.state = FaultPlanExecutionStateEnum.EXECUTING

    def enqueue_plan(self, plan: FaultPlanModel) -> bool:
        """
        Queue a fault plan for execution if the execution slot is available.

        Args:
            plan: Fault plan to queue.

        Returns:
            True if the plan was successfully queued, False otherwise.
        """
        if not self.is_available:
            raise RuntimeError("Runner is busy, cannot queue at the moment.")

        self._executor.plan = plan
        self._executor.state = FaultPlanExecutionStateEnum.QUEUED
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
        agent_handler_cls: Type[AgentStateHandler] = AgentStateHandler,
        plan_execution_handler_cls: Type[FaultPlanExecutionHandler] = (
            FaultPlanExecutionHandler
        ),
    ):
        self._state = AgentStateModel()

        self.agent = agent_handler_cls(agent=self._state)
        self.executor = plan_execution_handler_cls(executor=self._state.executor)
