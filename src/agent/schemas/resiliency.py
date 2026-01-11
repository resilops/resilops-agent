from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExecutionPolicy(BaseModel):
    """Defines how a resiliency plan is executed."""

    mode: str = Field(
        ...,
        description="Execution mode for the plan (e.g. 'serial', 'parallel').",
        examples=["serial", "parallel"],
    )
    stop_on_failure: bool = Field(
        ...,
        description="Whether execution should stop on the first experiment failure.",
    )


class ResiliencyPlan(BaseModel):
    """Represents a resiliency plan definition returned by the control plane."""

    id: Optional[int] = Field(
        default=None, description="Unique identifier of the resiliency plan."
    )
    run_id: Optional[int] = Field(
        default=None, description="Identifier of the current execution run."
    )
    title: str = Field(..., description="Human-readable title of the plan.")
    available: bool = Field(
        default=False,
        description="Whether the plan is currently available for execution.",
    )
    tags: List[str] = Field(
        default_factory=list, description="Tags associated with the plan."
    )
    execution: Optional[ExecutionPolicy] = Field(
        default=None, description="Execution policy for the plan."
    )
    experiments: List[int] = Field(
        default_factory=list,
        description="Ordered list of experiment IDs included in the plan.",
    )


class ExperimentSpec(BaseModel):
    """Specification for a resilience experiment."""

    name: str = Field(
        ...,
        description="Name of the experiment class in resilience-lib.",
    )
    args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments required to initialize the experiment.",
    )


class ProbeSpec(BaseModel):
    """Specification for a probe used to evaluate system behavior."""

    name: str = Field(
        ...,
        description="Name of the probe class in resilience-lib.",
    )
    args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments required to initialize the probe.",
    )


class Experiment(BaseModel):
    """Full experiment definition including execution and evaluation details."""

    id: int = Field(..., description="Unique identifier of the experiment.")
    title: str = Field(..., description="Human-readable experiment title.")
    description: str = Field(
        ..., description="Description of what the experiment does."
    )
    experiment: ExperimentSpec = Field(
        ..., description="Experiment implementation details."
    )
    probe: ProbeSpec = Field(
        ..., description="Probe used to evaluate experiment outcome."
    )
