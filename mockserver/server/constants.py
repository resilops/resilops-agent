from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel

ERROR_RATE = 0.2  # Probability of simulating a failure
MAX_DELAY = 2.0  # Maximum artificial delay in seconds
RESILIENCY_SUITE_EMPTY_RATE = 0.5  # 50 % of times suite is empty


RESILIENCY_EMPTY_SUITE = {}

RESILIENCY_SUITE = {
    "id": 1,
    "run_id": 2,
    "title": "Resiliency Suite 1",
    "tags": ["kubernetes"],
    "execution": {
        "mode": "series",  # Supports only "series" for now
        "stop_on_failure": True,  # stop executing further steps if one fails
    },
    "scenarios": [
        1,
    ],
}

RESILIENCY_SCENARIO = {
    "id": 1,
    "suite_id": 1,
    "title": "Do we remain available in face of pod going down?",
    "description": (
        "We expect Kubernetes to handle the situation gracefully when "
        "a pod goes down"
    ),
    "guardrail": {
        "name": "validate_pod_termination_guardrail",
        "kwargs": {
            "respect_pdb": True,
            "namespace": "abc",
            "labels": "app=myapp,tier=backend",
            "quantity": 25,
            "mode": "percentage",
        },
    },
    "action": {
        "name": "terminate_pods",
        "kwargs": {
            "namespace": "abc",
            "labels": "app=myapp,tier=backend",
            "quantity": 25,
            "mode": "percentage",
        },
    },
    "observer": {
        "name": "measure_http_latency",
        "kwargs": {
            "endpoint": "/health",
            "namespace": "abc",
            "labels": "app=myapp,tier=backend",
        },
        "sampling_interval": 3,
        "warmup_period": 10,
        "grace_period": 10,
    },
    "rollback": {
        "name": "wait_for_workload_stability",
        "kwargs": {
            "namespace": "abc",
            "labels": "app=myapp,tier=backend",
            "wait_period": 60,
        },
    },
}


class ResiliencySuiteStatusEnum(Enum):

    QUEUED: str = "queued"
    PROCESSED: str = "processed"


class ResiliencySuite(BaseModel):

    suite: Dict[str, Any]
    scenarios: List[Dict[str, Any]]
    state: ResiliencySuiteStatusEnum = ResiliencySuiteStatusEnum.QUEUED
