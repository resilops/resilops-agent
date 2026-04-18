from pydantic import UUID4, BaseModel, Field
from reslib.schemas.scenario import ResiliencyScenario as LibResiliencyScenario

from agent.constants import ScenarioClaimStatus


class ScenarioRun(BaseModel):
    """Scenario model returned by the control plane."""

    id: int = Field(..., description="Run ID")
    scenario_id: int = Field(..., description="Workload scenario ID")
    config: LibResiliencyScenario


class ScenarioClaim(BaseModel):
    """Claim model representing a scheduled scenario assignment."""

    id: UUID4 = Field(..., description="Claim id")
    run_id: int = Field(..., description="Resiliency scenario run id")
    scenario_id: int = Field(..., description="Scenario id")
    status: ScenarioClaimStatus = Field(default=None, description="Claim status")
