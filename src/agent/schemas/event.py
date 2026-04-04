from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field


class EventEnum(Enum):
    """All events enum"""

    SUITE_QUEUED = "res:agent:event:suite:queued"
    SUITE_EXECUTING = "res:agent:event:suite:executing"
    SUITE_EXECUTION_SUCCESS = "res:agent:event:suite:execution:success"
    SUITE_EXECUTION_FAILED = "res:agent:event:suite:execution:failed"


class EventPayload(BaseModel):
    """Base event payload that allows arbitrary additional fields."""

    event_name: EventEnum = Field(..., description="Name of the event.")
    type: str = Field(default="event", description="Event payload")
    error: Optional[str] = Field(default=None, description="Any error class")
    data: Optional[Dict] = Field(default=None, description="Results of the event.")
