from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field


class FaultPlanEventTypeEnum(str, Enum):
    """Types of events related to the lifecycle of a fault plan."""

    PLAN_RECEIVED = "plan:received"
    PLAN_ACKNOWLEDGED = "plan:acknowledged"
    PLAN_EXECUTING = "plan:executing"
    PLAN_EXECUTION_SUCCESS = "plan:execution:success"
    PLAN_EXECUTION_FAILED = "plan:execution:failed"
    PLAN_EXECUTION_ABORTED = "plan:execution:aborted"


class FaultEventType(str, Enum):
    """Types of events related to the execution of individual faults."""

    FAULT_EXECUTING = "fault:executing"
    FAULT_EXECUTION_ERROR = "fault:execution:error"
    FAULT_EXECUTION_TIMEOUT = "fault:execution:timeout"
    FAULT_ROLLBACK_SUCCESS = "fault:rollback"
    FAULT_ROLLBACK_ERROR = "fault:rollback:error"


class FaultEventModel(BaseModel):
    """Represents a single event related to the execution or rollback of a fault."""

    id: int
    plan_id: int
    type: FaultEventType
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FaultPlanEventModel(BaseModel):
    """Represents an event in the lifecycle of a fault plan."""

    id: int
    type: FaultPlanEventTypeEnum
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


AgentEventModel = Union[FaultPlanEventModel, FaultEventType]
