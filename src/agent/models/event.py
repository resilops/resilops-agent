from enum import Enum


class AgentEventEnum(str, Enum):
    """All events enum"""

    PLAN_QUEUED = "plan:queued"
    PLAN_EXECUTING = "plan:executing"
    PLAN_EXECUTION_SUCCESS = "plan:execution:success"
    PLAN_EXECUTION_FAILED = "plan:execution:failed"

    FAULT_EXECUTION_ERROR = "fault:execution:error"
