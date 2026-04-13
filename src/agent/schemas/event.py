from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field


class EventEnum(Enum):
    """Event names emitted by the agent."""

    SCENARIO_QUEUED = "res:agent:event:scenario:queued"
    SCENARIO_EXECUTING = "res:agent:event:scenario:executing"
    SCENARIO_EXECUTION_SUCCESS = "res:agent:event:scenario:execution:success"
    SCENARIO_EXECUTION_FAILED = "res:agent:event:scenario:execution:failed"
    DISCOVERY_SUCCESS = "res:agent:event:discovery:success"
    DISCOVERY_FAILED = "res:agent:event:discovery:failed"


class EventPayload(BaseModel):
    """Base event payload that allows arbitrary additional fields."""

    event_name: EventEnum = Field(..., description="Name of the event.")
    type: str = Field(default="event", description="Event payload")
    source: str = Field(default="agent", description="Source of the event.")
    error: Optional[str] = Field(default=None, description="Any error class")
    data: Optional[Dict] = Field(default=None, description="Results of the event.")
