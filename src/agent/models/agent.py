import asyncio
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from agent.models.fault import FaultPlanResponseModel


class AgentStateEnum(str, Enum):
    """Represents the overall health state of the agent."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class RunnerStateEnum(str, Enum):
    """Represents the execution state of the fault plan runner."""

    EXECUTING = "executing"
    QUEUED = "queued"
    AVAILABLE = "available"


class RunnerStateModel(BaseModel):
    """
    In-memory state of the fault plan runner.

    Tracks the currently assigned fault plan and its execution state.
    """

    plan: Optional[FaultPlanResponseModel] = None
    state: RunnerStateEnum = RunnerStateEnum.AVAILABLE

    @property
    def available(self) -> bool:
        """Return True if the runner is ready to accept a new plan."""
        return self.state == RunnerStateEnum.AVAILABLE

    @property
    def queued(self) -> bool:
        """Return True if a plan is queued for execution."""
        return self.state == RunnerStateEnum.QUEUED

    @property
    def executing(self) -> bool:
        """Return True if a plan is currently executing."""
        return self.state == RunnerStateEnum.EXECUTING

    def reset(self) -> None:
        """
        Clear the current plan and mark the runner as available.
        This should be called after successful execution or failure.
        """
        self.plan = None
        self.state = RunnerStateEnum.AVAILABLE

    def enqueue(self, plan: FaultPlanResponseModel) -> None:
        """
        Assign a fault plan to the runner and mark it as queued.

        Args:
            plan: Fault plan to be executed.
        """
        self.plan = plan
        self.state = RunnerStateEnum.QUEUED

    def mark_executing(self) -> None:
        """Mark the runner as actively executing a fault plan."""
        self.state = RunnerStateEnum.EXECUTING


class AgentStateModel(BaseModel):
    """
    In-memory runtime state of the agent.

    This model tracks agent health, runner state, and currently running
    periodic tasks. It is not intended for persistence or API serialization.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: AgentStateEnum = AgentStateEnum.UNKNOWN
    runner: RunnerStateModel = Field(default_factory=RunnerStateModel)
    running_tasks: List[asyncio.Task] = Field(default_factory=list)

    @property
    def healthy(self) -> bool:
        """
        Return True if the agent is healthy.
        Used by periodic tasks to determine whether execution should proceed.
        """
        return self.status == AgentStateEnum.HEALTHY

    @healthy.setter
    def healthy(self, value: bool) -> None:
        """
        Set the agent's health status.

        Args:
            value: True to mark as HEALTHY, False as UNHEALTHY.
        """
        self.status = AgentStateEnum.HEALTHY if value else AgentStateEnum.UNHEALTHY

    def set_running_tasks(self, tasks: List[asyncio.Task]) -> None:
        """
        Register periodic tasks as currently running.

        Args:
            tasks: List of started periodic task instances.
        """
        self.running_tasks = tasks
