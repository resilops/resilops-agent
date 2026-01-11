ERROR_RATE = 0.2  # Probability of simulating a failure
MAX_DELAY = 2.0  # Maximum artificial delay in seconds
RESILIENCY_PLAN_EMPTY_RATE = 0.5  # 50 % of times plan is empty


RESILIENCY_EMPTY_PLAN = {"available": False, "title": "No plan available at the moment"}

RESILIENCY_PLAN = {
    "id": 123,
    "run_id": 123,
    "title": "Resiliency Plan 1",
    "tags": ["kubernetes"],
    "available": True,
    "execution": {
        "mode": "series",  # Supports only "series" for now
        "stop_on_failure": True,  # stop executing further steps if one fails
    },
    "experiments": [1, 2, 3],
}

EXPERIMENT_EXAMPLE = {
    "id": 234,
    "plan_id": 123,
    "title": "Do we remain available in face of pod going down?",
    "description": (
        "We expect Kubernetes to handle the situation gracefully when a pod goes down"
    ),
    "guardrail": {
        "name": "is_pod_termination_possible",
        "kwargs": {"respect_pdb": True},
    },
    "experiment": {
        "name": "terminate_pods",
        "kwargs": {
            "namespace": "abc",
            "label": "myapp",
            "quantity": 25,
            "mode": "percentage",
        },
    },
    "lifecycle": {
        "pre_experiment_delay": 5,
        "post_experiment_delay": 5,
        "post_probe_delay": 10,
    },
    "probe": {"name": "http_readiness_probe", "kwargs": {"endpoint": "", "timeout": 3}},
    "rollback": {"name": "rollback_pod_kill", "kwargs": {"cmd": "asd"}},
}
