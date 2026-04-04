from typing import List, Optional

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
