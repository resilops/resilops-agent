from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel

ERROR_RATE = 0.2  # Probability of simulating a failure
MAX_DELAY = 2.0  # Maximum artificial delay in seconds
RESILIENCY_SUITE_EMPTY_RATE = 0.5  # 50 % of times suite is empty


class ResiliencySuiteStatusEnum(Enum):

    QUEUED = "queued"
    PROCESSED = "processed"


class ResiliencySuite(BaseModel):

    suite: Dict[str, Any]
    scenarios: List[Dict[str, Any]]
    state: ResiliencySuiteStatusEnum = ResiliencySuiteStatusEnum.QUEUED
