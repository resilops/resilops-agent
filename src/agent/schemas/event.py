from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentEventEnum(str, Enum):
    """All events enum"""

    SUITE_QUEUED = "agent:suite:queued"
    SUITE_EXECUTING = "agent:suite:executing"
    SUITE_EXECUTION_SUCCESS = "agent:suite:execution:success"
    SUITE_EXECUTION_FAILED = "agent:suite:execution:failed"


class AgentEventPayload(BaseModel):
    """Base event payload that allows arbitrary additional fields."""

    model_config = ConfigDict(extra="allow")

    event_name: AgentEventEnum = Field(..., description="Name of the event.")
    is_error: bool = Field(default=False, description="Is this event error related")
    error_msg: Optional[str] = Field(default=None, description="Error message")
