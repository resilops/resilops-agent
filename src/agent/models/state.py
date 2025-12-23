import asyncio
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from agent.models.fault import FaultPlanModel


class AgentStateEnum(str, Enum):
    """Represents the overall health state of the agent."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class FaultPlanExecutionStateEnum(str, Enum):
    """Represents the execution state of the fault plan runner."""

    EXECUTING = "executing"
    QUEUED = "queued"
    AVAILABLE = "available"


class FaultPlanExecutionStateModel(BaseModel):
    """
    In-memory state of the fault plan runner.

    Tracks the currently assigned fault plan and its execution state.
    """

    plan: Optional[FaultPlanModel] = None
    state: FaultPlanExecutionStateEnum = FaultPlanExecutionStateEnum.AVAILABLE


class AgentStateModel(BaseModel):
    """
    In-memory runtime state of the agent.

    This model tracks agent health, runner state, and currently running
    periodic tasks. It is not intended for persistence or API serialization.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: AgentStateEnum = AgentStateEnum.UNKNOWN
    executor: FaultPlanExecutionStateModel = Field(
        default_factory=FaultPlanExecutionStateModel
    )
    running_workers: List[asyncio.Task] = Field(default_factory=list)
