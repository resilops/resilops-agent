import asyncio
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from agent.schemas.resiliency import ResiliencyPlanModel


class AgentStateEnum(str, Enum):
    """Represents the overall health state of the agent."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ResiliencyPlanExecutionStateEnum(str, Enum):
    """Represents the execution state of the resiliency plan runner."""

    EXECUTING = "executing"
    QUEUED = "queued"
    AVAILABLE = "available"


class ResiliencyPlanExecutionStateModel(BaseModel):
    """
    In-memory state of the resiliency plan runner.

    Tracks the currently assigned plan step and its execution state.
    """

    plan: Optional[ResiliencyPlanModel] = None
    state: ResiliencyPlanExecutionStateEnum = ResiliencyPlanExecutionStateEnum.AVAILABLE


class AgentStateModel(BaseModel):
    """
    In-memory runtime state of the agent.

    This model tracks agent health, runner state, and currently running
    periodic tasks. It is not intended for persistence or API serialization.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: AgentStateEnum = AgentStateEnum.UNKNOWN
    executor: ResiliencyPlanExecutionStateModel = Field(
        default_factory=ResiliencyPlanExecutionStateModel
    )
    running_workers: List[asyncio.Task] = Field(default_factory=list)
