import asyncio
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from agent.schemas.scenario import ResiliencyScenarioClaim


class AgentHealthStatusEnum(str, Enum):
    """Represents the overall health of the agent."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class RunnerLifecycleStateEnum(str, Enum):
    """Represents the execution state of the resiliency scenario runner."""

    RUNNING = "running"
    QUEUED = "queued"
    IDLE = "idle"


class RunnerRuntimeState(BaseModel):
    """
    In-memory runtime state of resiliency scenario processing.

    Tracks the currently assigned scenario and its lifecycle state.
    """

    claim: Optional[ResiliencyScenarioClaim] = None
    state: RunnerLifecycleStateEnum = RunnerLifecycleStateEnum.IDLE


class AgentRuntimeState(BaseModel):
    """
    In-memory runtime state of the agent.

    Tracks agent health, resiliency scenario lifecycle, and active workers.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    health: AgentHealthStatusEnum = AgentHealthStatusEnum.UNKNOWN
    runner: RunnerRuntimeState = Field(default_factory=RunnerRuntimeState)
    running_workers: List[asyncio.Task] = Field(default_factory=list)
