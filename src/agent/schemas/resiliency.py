from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExecutionPolicy(BaseModel):
    """
    Defines how a resiliency plan is executed.
    """

    mode: str = Field(
        ...,
        description="Execution mode for the plan (e.g. 'serial', 'parallel').",
        examples=["serial", "parallel"],
    )
    stop_on_failure: bool = Field(
        ...,
        description="Whether execution should stop on the first failure.",
    )


class ResiliencyPlan(BaseModel):
    """
    Represents a resiliency plan definition returned by the control plane.
    """

    id: Optional[int] = Field(
        default=None,
        description="Unique identifier of the resiliency plan.",
    )
    run_id: Optional[int] = Field(
        default=None,
        description="Identifier of the current execution run.",
    )
    title: str = Field(
        ...,
        description="Human-readable title of the plan.",
    )
    available: bool = Field(
        default=False,
        description="Whether the plan is currently available for execution.",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags associated with the plan.",
    )
    execution: Optional[ExecutionPolicy] = Field(
        default=None,
        description="Execution policy applied to this plan.",
    )
    experiments: List[int] = Field(
        default_factory=list,
        description="Ordered list of experiment IDs included in the plan.",
    )


class CallableSpec(BaseModel):
    """Base specification for a callable entity in resilience-lib."""

    name: str = Field(
        ...,
        description="Name of the callable in resilience-lib.",
    )
    kwargs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Keyword arguments passed to the callable.",
    )


class GuardRailSpec(CallableSpec):
    """Specification for a guard rail that enforces safety conditions."""


class ExperimentSpec(CallableSpec):
    """Specification for a resilience experiment."""


class ProbeSpec(CallableSpec):
    """Specification for a probe used to evaluate system behavior."""


class RollbackSpec(CallableSpec):
    """Specification for rollback logic used to restore system state."""


class LifecycleSpec(BaseModel):
    """Optional lifecycle delays for an experiment execution."""

    pre_experiment_delay: Optional[int] = Field(
        default=None, description="Delay in seconds before executing the experiment."
    )
    post_experiment_delay: Optional[int] = Field(
        default=None,
        description="Delay in seconds after the experiment but before the probe.",
    )
    post_probe_delay: Optional[int] = Field(
        default=None, description="Delay in seconds after probe completion."
    )


class ExperimentDefinition(BaseModel):
    """Full experiment definition including execution, validation, and rollback."""

    id: int = Field(
        ...,
        description="Unique identifier of the experiment.",
    )
    title: str = Field(
        ...,
        description="Human-readable experiment title.",
    )
    description: str = Field(
        ...,
        description="Description of what the experiment does.",
    )
    guardrail: Optional[GuardRailSpec] = Field(
        default=None,
        description="Optional guard rail executed before or during the experiment.",
    )
    experiment: ExperimentSpec = Field(
        ...,
        description="Fault injection logic.",
    )
    probe: ProbeSpec = Field(
        ...,
        description="Probe used to evaluate experiment outcome.",
    )
    rollback: Optional[RollbackSpec] = Field(
        default=None,
        description="Optional rollback logic to restore system state.",
    )
    lifecycle: Optional[LifecycleSpec] = Field(
        default=None,
        description="Optional lifecycle delays for pre/post experiment and probe.",
    )
