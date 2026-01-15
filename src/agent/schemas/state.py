import asyncio
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from agent.schemas.suite import ResiliencySuite


class AgentHealthStatusEnum(str, Enum):
    """Represents the overall health of the agent."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ResiliencySuiteLifecycleStateEnum(str, Enum):
    """Represents the execution state of the resiliency suite runner."""

    RUNNING = "running"
    QUEUED = "queued"
    IDLE = "idle"


class ResiliencySuiteRuntimeState(BaseModel):
    """
    In-memory runtime state of resiliency suite processing.

    Tracks the currently assigned suite and its lifecycle state.
    """

    suite: Optional[ResiliencySuite] = None
    state: ResiliencySuiteLifecycleStateEnum = ResiliencySuiteLifecycleStateEnum.IDLE


class AgentRuntimeState(BaseModel):
    """
    In-memory runtime state of the agent.

    Tracks agent health, resiliency suite lifecycle, and active workers.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    health: AgentHealthStatusEnum = AgentHealthStatusEnum.UNKNOWN
    runner: ResiliencySuiteRuntimeState = Field(
        default_factory=ResiliencySuiteRuntimeState
    )
    running_workers: List[asyncio.Task] = Field(default_factory=list)
