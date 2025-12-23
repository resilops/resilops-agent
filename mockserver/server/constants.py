ERROR_RATE = 0.2  # Probability of simulating a failure
MAX_DELAY = 2.0  # Maximum artificial delay in seconds
FAULT_PLAN_EMPTY_RATE = 0.5  # 50 % of times fault is empty


FAULT_EMPTY_PLAN = {"available": False, "title": "No plan available at the moment"}

FAULT_PLAN = {
    "id": 123,
    "run_id": 123,
    "title": "Fault Plan 1",
    "available": True,
    "execution": {
        "mode": "series",  # Supports only "series" for now
        "stop_on_failure": True,  # stop executing further faults if one fails
    },
    "faults": [1, 2, 3],
}

FAULT_EXAMPLE = {
    "title": "Do we remain available in face of pod going down?",
    "description": (
        "We expect Kubernetes to handle the situation gracefully when a pod goes down"
    ),
    "tags": ["kubernetes"],
    "steady-state-hypothesis": {
        "title": "Verifying service remains healthy",
        "probes": [
            {
                "name": "all-our-microservices-should-be-healthy",
                "type": "probe",
                "tolerance": True,
                "secrets": ["k8s"],
                "provider": {
                    "type": "python",
                    "module": "chaosk8s.probes",
                    "func": "microservice_available_and_healthy",
                    "arguments": {"name": "myapp"},
                },
            }
        ],
    },
    "method": [
        {
            "type": "action",
            "name": "terminate-db-pod",
            "secrets": ["k8s"],
            "provider": {
                "type": "python",
                "module": "chaosk8s.pod.actions",
                "func": "terminate_pods",
                "arguments": {
                    "label_selector": "app=my-app",
                    "name_pattern": "my-app-[0-9]$",
                    "rand": True,
                },
            },
            "pauses": {"after": 5},
        }
    ],
}
