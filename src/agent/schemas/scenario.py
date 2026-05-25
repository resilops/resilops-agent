from pydantic import UUID4, BaseModel, Field
from reslib.schemas.scenario import ResiliencyScenario as LibResiliencyScenario

from agent.constants import ScenarioClaimSetExecutionMode, ScenarioClaimStatus


class ScenarioRun(BaseModel):
    """Scenario model returned by the control plane."""

    id: int = Field(..., description="Run ID")
    scenario_id: int = Field(..., description="Workload scenario ID")
    config: LibResiliencyScenario


class ScenarioClaim(BaseModel):
    """Claim model representing one scenario in a claim set."""

    id: UUID4 = Field(..., description="Claim id")
    run_id: int = Field(..., description="Resiliency scenario run id")
    scenario_id: int = Field(..., description="Scenario id")
    position: int = Field(..., description="Claim execution position")


class ScenarioClaimSet(BaseModel):
    """Ordered claim set assigned to one workload."""

    id: UUID4 = Field(..., description="Claim set id")
    workload_id: int = Field(..., description="Workload id")
    quality_gate_run_id: int | None = Field(
        default=None,
        description="Quality gate run id when this set belongs to a quality gate",
    )
    execution_mode: ScenarioClaimSetExecutionMode = Field(
        default=ScenarioClaimSetExecutionMode.stop_on_failure,
        description="Claim set execution mode",
    )
    status: ScenarioClaimStatus = Field(default=None, description="Claim set status")
    claims: list[ScenarioClaim] = Field(
        ...,
        min_length=1,
        description="Ordered scenario claims in this set",
    )
