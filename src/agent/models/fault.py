from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExecutionModel(BaseModel):
    """Execution configuration for a fault plan."""

    mode: str = Field(..., description="Execution mode, e.g., 'series' or 'parallel'")
    stop_on_failure: bool = Field(
        ..., description="Whether to stop execution on first failure"
    )


class FaultPlanModel(BaseModel):
    """Represents a full fault plan returned by the control plane."""

    id: Optional[int] = None
    run_id: Optional[int] = None
    title: str
    available: bool = False
    execution: Optional[ExecutionModel] = None
    faults: List[int] = Field(default_factory=list)


class FaultModel(BaseModel):

    id: int
    title: str
    description: str
    tags: List[str] = Field(default_factory=list)
    steady_state_hypothesis: Dict[Any, Any] = Field(
        default_factory=dict, alias="steady-state-hypothesis"
    )
    method: List[Dict[Any, Any]] = Field(default_factory=list)
