from pydantic import BaseModel, Field
from reslib.schemas.scenario import ResiliencyScenario as LibResiliencyScenario

from agent.constants import ResiliencyScenarioClaimStatusEnum


class ResiliencyScenario(LibResiliencyScenario):
    """Scenario model returned by the control plane."""

    id: int = Field(..., description="Scenario id")
    run_id: int = Field(..., description="Resiliency scenario run id")


class ResiliencyScenarioClaim(BaseModel):
    """Claim model representing a scheduled scenario assignment."""

    id: int = Field(..., description="Claim id")
    run_id: int = Field(..., description="Resiliency scenario run id")
    scenario_id: int = Field(..., description="Scenario id")
    status: ResiliencyScenarioClaimStatusEnum = Field(
        default=None, description="Claim status"
    )
