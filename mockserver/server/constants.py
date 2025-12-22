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
        "mode": "series",  # "series" or "parallel"
        "stop_on_failure": True,  # stop executing further faults if one fails
    },
    "faults": [
        {
            "id": 123,
            "type": "pod:kill",
            "context": {"namespace": "default", "pod_name": "nginx-123"},
        },
        {"id": 124, "type": "node:drain", "context": {"node_name": "worker-1"}},
    ],
}
