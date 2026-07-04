from types import SimpleNamespace
from unittest.mock import Mock, patch

from agent.handlers.telemetry import AgentTelemetry, RunTelemetry
from agent.schemas.event import EventEnum, EventPayload


def test_log_emits_structured_payload():
    payload = SimpleNamespace(model_dump=lambda **kwargs: {"field": "value"})

    with patch("agent.handlers.telemetry.uuid.uuid4", return_value="ingest-1"):
        with patch("agent.handlers.telemetry.logger.info") as info_mock:
            AgentTelemetry._log(name="evt", payload=payload, run_id=9)

    info_mock.assert_called_once_with(
        "evt",
        extra={"field": "value", "ingest_id": "ingest-1", "run_id": 9},
    )


def test_emit_event_and_metrics_use_payload_names():
    telemetry = AgentTelemetry()
    event = EventPayload(event_name=EventEnum.SCENARIO_QUEUED)
    metrics = SimpleNamespace(metrics_name=SimpleNamespace(value="metric.name"))

    with patch.object(telemetry, "_log") as log_mock:
        telemetry.emit_event(event=event, run_id=1)
        telemetry.emit_metrics(metrics=metrics, run_id=2)

    assert log_mock.call_args_list[0].kwargs["name"] == EventEnum.SCENARIO_QUEUED.value
    assert log_mock.call_args_list[0].kwargs["run_id"] == 1
    assert log_mock.call_args_list[1].kwargs["name"] == "metric.name"
    assert log_mock.call_args_list[1].kwargs["run_id"] == 2


def test_run_telemetry_binds_run_id():
    telemetry = Mock()
    run_telemetry = RunTelemetry(telemetry=telemetry, run_id=44)
    event = EventPayload(event_name=EventEnum.SCENARIO_QUEUED)
    metrics = object()

    run_telemetry.emit_event(event=event)
    run_telemetry.emit_metrics(metrics=metrics)

    telemetry.emit_event.assert_called_once_with(event=event, run_id=44)
    telemetry.emit_metrics.assert_called_once_with(metrics=metrics, run_id=44)
