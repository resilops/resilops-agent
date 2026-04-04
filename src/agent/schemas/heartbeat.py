from typing import Optional

from pydantic import BaseModel, Field

from agent.constants import AgentHealthEnum


class HeartbeatRequestModel(BaseModel):
    """Request schema for heartbeat endpoint"""

    health: AgentHealthEnum = Field(
        default=AgentHealthEnum.healthy,
        description="Current self-reported health of the agent",
    )
    version: str = Field(
        ...,
        max_length=10,
        description="Agent version",
    )
    config_version: str = Field(
        ...,
        max_length=50,
        description="Agent configuration version",
    )
    reason: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Short reason when health is degraded",
    )


class HeartbeatResponseModel(BaseModel):
    """Heartbeat response from the control plane."""

    health: AgentHealthEnum = Field(..., description="Status of the agent")
