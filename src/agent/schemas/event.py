from enum import Enum


class AgentEventEnum(str, Enum):
    """All events enum"""

    PLAN_QUEUED = "agent:plan:queued"
    PLAN_EXECUTING = "agent:plan:executing"
    PLAN_EXECUTION_SUCCESS = "agent:plan:execution:success"
    PLAN_EXECUTION_FAILED = "agent:plan:execution:failed"
