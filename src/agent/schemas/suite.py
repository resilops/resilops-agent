from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExecutionPolicy(BaseModel):
    """Defines how a resiliency suite is executed."""

    mode: str = Field(
        ...,
        description="Execution mode for the suite (e.g., 'series', 'parallel').",
        examples=["series", "parallel"],
    )
    stop_on_failure: bool = Field(
        ...,
        description="Whether execution should stop on the first failure.",
    )


class ResiliencySuite(BaseModel):
    """
    Represents a resiliency suite returned by the control plane.
    """

    id: int = Field(..., description="Unique identifier of the suite.")
    run_id: int = Field(..., description="Identifier of the current execution run.")
    title: str = Field(..., description="Human-readable title of the suite.")
    tags: List[str] = Field(
        default_factory=list, description="Tags associated with the suite."
    )
    execution: Optional[ExecutionPolicy] = Field(
        default=None, description="Execution policy applied to this suite."
    )
    scenarios: List[int] = Field(
        default_factory=list,
        description="Ordered list of scenario IDs included in the suite.",
    )


class Step(BaseModel):
    """
    Represents a single step in a scenario: guardrail, action, or rollback.

    `overrides` will be merged with the scenario template for this step.
    """

    type: str = Field(..., description="Step type")
    name: str = Field(..., description="Name of the callable in resilience-lib.")
    overrides: Dict[str, Any] = Field(
        default_factory=dict,
        description="Step-specific overrides for the template fields.",
    )


class Observer(BaseModel):
    """
    Observer configuration for monitoring metrics during scenario execution.

    - `config` contains timing-related parameters like sampling interval,
      warmup period, and grace period.
    - `kwargs` contains arguments passed to the observer callable.
    """

    name: str = Field(..., description="Name of the observer callable.")
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Observer-specific config like sampling_interval, "
            "warmup_period, grace_period."
        ),
    )
    kwargs: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments passed to the observer callable."
    )


class ResiliencyScenario(BaseModel):
    """
    Full scenario definition including:

    - `template`: shared arguments for all steps
    - `steps`: ordered steps (guardrail, action, rollback)
    - `observer`: passive monitoring
    """

    id: int = Field(..., description="Unique identifier of the scenario.")
    suite_id: int = Field(..., description="Identifier of the parent suite.")
    title: str = Field(..., description="Human-readable scenario title.")
    description: str = Field(..., description="Description of what the scenario tests.")
    template: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Scenario-specific template fields, merged into all steps. "
            "Can be any kwargs depending on scenario type."
        ),
    )
    steps: List[Step] = Field(
        ..., description="Ordered list of guardrail/action/rollback steps."
    )
    observer: Observer = Field(
        ..., description="Observer configuration to monitor system behavior."
    )
