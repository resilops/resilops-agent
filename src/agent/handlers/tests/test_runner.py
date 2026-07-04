from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from agent.constants import ScenarioClaimSetExecutionMode
from agent.handlers.runner import ScenarioRunner
from agent.schemas.event import EventEnum, EventPayload
from agent.schemas.scenario import ScenarioClaim, ScenarioClaimSet


def _claim(position: int, run_id: int) -> ScenarioClaim:
    return ScenarioClaim(
        id=uuid4(),
        run_id=run_id,
        scenario_id=run_id + 10,
        position=position,
    )


def test_emit_claim_event_uses_claim_run_id():
    telemetry = Mock()
    runner = ScenarioRunner(client=Mock(), telemetry=telemetry)
    claim = _claim(position=1, run_id=22)

    runner._emit_claim_event(EventEnum.SCENARIO_EXECUTING, claim, data={"ok": True})

    emitted_event = telemetry.emit_event.call_args.kwargs["event"]
    assert isinstance(emitted_event, EventPayload)
    assert emitted_event.event_name == EventEnum.SCENARIO_EXECUTING
    assert telemetry.emit_event.call_args.kwargs["run_id"] == 22


@pytest.mark.asyncio
async def test_execute_claim_uses_run_bound_telemetry(sample_run_config):
    client = Mock()
    client.fetch_scenario_run = AsyncMock(
        return_value=SimpleNamespace(id=77, config=sample_run_config)
    )
    telemetry = Mock()
    runner = ScenarioRunner(client=client, telemetry=telemetry)

    with patch(
        "agent.handlers.runner.execute_resilience_scenario", new=AsyncMock()
    ) as execute_mock:
        await runner.execute_claim(_claim(position=1, run_id=77))

    execute_mock.assert_awaited_once()
    assert execute_mock.await_args.kwargs["scenario"] is sample_run_config
    assert execute_mock.await_args.kwargs["telemetry"].run_id == 77


@pytest.mark.asyncio
async def test_execute_claim_set_stops_on_failure():
    claim1 = _claim(position=2, run_id=2)
    claim2 = _claim(position=1, run_id=1)
    claim_set = ScenarioClaimSet(
        id=uuid4(),
        workload_id=1,
        status="pending",
        execution_mode=ScenarioClaimSetExecutionMode.stop_on_failure,
        claims=[claim1, claim2],
    )
    runner = ScenarioRunner(client=Mock(), telemetry=Mock())
    error = RuntimeError("boom")
    runner.execute_claim = AsyncMock(side_effect=[None, error])

    with patch("agent.handlers.runner.time.sleep") as sleep_mock:
        with pytest.raises(RuntimeError) as exc_info:
            await runner.execute_claim_set(claim_set)

    assert exc_info.value.result["claim"] == claim1
    assert (
        runner.telemetry.emit_event.call_args_list[0].kwargs["run_id"] == claim2.run_id
    )
    assert runner.telemetry.emit_event.call_args_list[-1].kwargs[
        "event"
    ].event_name == (EventEnum.SCENARIO_EXECUTION_FAILED)
    assert sleep_mock.call_count == 1


@pytest.mark.asyncio
async def test_execute_claim_set_continues_when_configured():
    claim1 = _claim(position=1, run_id=1)
    claim2 = _claim(position=2, run_id=2)
    claim_set = ScenarioClaimSet(
        id=uuid4(),
        workload_id=1,
        status="pending",
        execution_mode=ScenarioClaimSetExecutionMode.continue_on_failure,
        claims=[claim1, claim2],
    )
    runner = ScenarioRunner(client=Mock(), telemetry=Mock())
    runner.execute_claim = AsyncMock(side_effect=[RuntimeError("boom"), None])

    with patch("agent.handlers.runner.time.sleep"):
        await runner.execute_claim_set(claim_set)

    event_names = [
        call.kwargs["event"].event_name
        for call in runner.telemetry.emit_event.call_args_list
    ]
    assert event_names == [
        EventEnum.SCENARIO_EXECUTING,
        EventEnum.SCENARIO_EXECUTION_FAILED,
        EventEnum.SCENARIO_EXECUTING,
        EventEnum.SCENARIO_EXECUTION_SUCCESS,
    ]
