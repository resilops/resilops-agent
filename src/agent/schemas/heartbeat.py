from pydantic import BaseModel, Field


class HeartbeatResponseModel(BaseModel):
    """Heartbeat response from the control plane."""

    status: str = Field(..., description="Status of the agent, e.g., 'ok'")
