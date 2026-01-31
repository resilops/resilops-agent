from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EventEnum(str, Enum):
    """All events enum"""

    SUITE_QUEUED = "res:agent:event:suite:queued"
    SUITE_EXECUTING = "res:agent:event:suite:executing"
    SUITE_EXECUTION_SUCCESS = "res:agent:event:suite:execution:success"
    SUITE_EXECUTION_FAILED = "res:agent:event:suite:execution:failed"


class EventPayload(BaseModel):
    """Base event payload that allows arbitrary additional fields."""

    model_config = ConfigDict(extra="allow")

    event_name: EventEnum = Field(..., description="Name of the event.")
    type: str = Field(default="event", description="Event payload")
    details: Optional[str] = Field(
        default=None, description="Any details about the event"
    )
