from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FaultResponseModel(BaseModel):
    """Represents a single fault within a fault plan."""

    id: int
    type: str
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Fault-specific context; schema depends on fault type",
    )


class ExecutionResponseModel(BaseModel):
    """Execution configuration for a fault plan."""

    mode: str = Field(..., description="Execution mode, e.g., 'series' or 'parallel'")
    stop_on_failure: bool = Field(
        ..., description="Whether to stop execution on first failure"
    )


class FaultPlanResponseModel(BaseModel):
    """Represents a full fault plan returned by the control plane."""

    id: Optional[int] = None
    run_id: Optional[int] = None
    title: str
    available: bool = False
    execution: Optional[ExecutionResponseModel] = None
    faults: List[FaultResponseModel] = Field(default_factory=list)

    async def execute(self) -> None:
        pass
