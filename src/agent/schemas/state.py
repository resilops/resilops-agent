import asyncio
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from agent.schemas.resiliency import ResiliencyPlan


class AgentHealthStatusEnum(str, Enum):
    """Represents the overall health of the agent."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ResiliencyPlanLifecycleStateEnum(str, Enum):
    """Represents the execution state of the resiliency plan runner."""

    RUNNING = "running"
    QUEUED = "queued"
    IDLE = "idle"


class ResiliencyPlanRuntimeState(BaseModel):
    """
    In-memory runtime state of resiliency plan processing.

    Tracks the currently assigned plan and its lifecycle state.
    """

    plan: Optional[ResiliencyPlan] = None
    state: ResiliencyPlanLifecycleStateEnum = ResiliencyPlanLifecycleStateEnum.IDLE


class AgentRuntimeState(BaseModel):
    """
    In-memory runtime state of the agent.

    Tracks agent health, resiliency plan lifecycle, and active workers.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    health: AgentHealthStatusEnum = AgentHealthStatusEnum.UNKNOWN
    runner: ResiliencyPlanRuntimeState = Field(
        default_factory=ResiliencyPlanRuntimeState
    )
    running_workers: List[asyncio.Task] = Field(default_factory=list)
