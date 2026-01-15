ERROR_RATE = 0.2  # Probability of simulating a failure
MAX_DELAY = 2.0  # Maximum artificial delay in seconds
RESILIENCY_SUITE_EMPTY_RATE = 0.5  # 50 % of times suite is empty


RESILIENCY_EMPTY_SUITE = {
    "available": False,
    "title": "No suite available at the moment",
}

RESILIENCY_SUITE = {
    "id": 123,
    "run_id": 123,
    "title": "Resiliency Suite 1",
    "tags": ["kubernetes"],
    "available": True,
    "execution": {
        "mode": "series",  # Supports only "series" for now
        "stop_on_failure": True,  # stop executing further steps if one fails
    },
    "scenarios": [1, 2, 3],
}

RESILIENCY_SCENARIO = {
    "id": 234,
    "suite_id": 123,
    "title": "Do we remain available in face of pod going down?",
    "description": (
        "We expect Kubernetes to handle the situation gracefully when "
        "a pod goes down"
    ),
    "guardrail": {
        "name": "is_pod_termination_possible",
        "kwargs": {
            "respect_pdb": True,
            "namespace": "abc",
            "label": "myapp",
            "quantity": 25,
            "mode": "percentage",
        },
    },
    "action": {
        "name": "terminate_pods",
        "kwargs": {
            "namespace": "abc",
            "label": "myapp",
            "quantity": 25,
            "mode": "percentage",
        },
    },
    "lifecycle": {
        "action": {
            "before": {"name": "", "kwargs": {}},
            "after": {"name": "", "kwargs": {}},
        },
        "rollback": {
            "before": {"name": "", "kwargs": {}},
            "after": {"name": "", "kwargs": {}},
        },
    },
    "observer": {
        "name": "http_latency_probe",
        "kwargs": {"endpoint": "/health", "timeout": 3},
        "grace_period": 10,
    },
    "rollback": {"name": "rollback_pod_kill", "kwargs": {"cmd": "asd"}},
}
