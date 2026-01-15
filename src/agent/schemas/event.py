from enum import Enum


class AgentEventEnum(str, Enum):
    """All events enum"""

    SUITE_QUEUED = "agent:suite:queued"
    SUITE_EXECUTING = "agent:suite:executing"
    SUITE_EXECUTION_SUCCESS = "agent:suite:execution:success"
    SUITE_EXECUTION_FAILED = "agent:suite:execution:failed"
