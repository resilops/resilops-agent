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


class CallableSpec(BaseModel):
    """Base specification for a callable entity in resilience-lib."""

    name: str = Field(..., description="Name of the callable in resilience-lib.")
    kwargs: Dict[str, Any] = Field(
        default_factory=dict, description="Keyword arguments passed to the callable."
    )


class GuardRailSpec(CallableSpec):
    """Specification for a guardrail that enforces safety conditions."""


class ActionSpec(CallableSpec):
    """Specification for a resilience action (e.g., pod kill, node drain)."""


class ObserverSpec(CallableSpec):
    """Specification for an observer that monitors system behavior."""

    sampling_interval: Optional[int] = Field(
        ..., description="Interval between observer samples in seconds."
    )
    warmup_period: Optional[int] = Field(
        ..., description="Observer warmup period in seconds"
    )
    grace_period: Optional[int] = Field(..., description="Grace period in seconds")


class RollbackSpec(CallableSpec):
    """Specification for rollback logic used to restore system state."""


class ResiliencyScenario(BaseModel):
    """Full scenario definition including execution, validation, and rollback."""

    id: int = Field(..., description="Unique identifier of the scenario.")
    suite_id: int = Field(..., description="Identifier of the parent suite.")
    title: str = Field(..., description="Human-readable scenario title.")
    description: str = Field(..., description="Description of what the scenario tests.")
    guardrail: Optional[GuardRailSpec] = Field(
        default=None, description="Optional guardrail executed before the action."
    )
    action: ActionSpec = Field(..., description="Fault injection or resilience action.")
    observer: ObserverSpec = Field(
        ..., description="Observer used to evaluate scenario outcome."
    )
    rollback: Optional[RollbackSpec] = Field(
        default=None, description="Optional rollback logic to restore system state."
    )
