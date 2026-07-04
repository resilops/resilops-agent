import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from agent.exceptions import APIRequestError
from agent.schemas.event import EventEnum
from agent.workers.scheduler import ScenarioSchedulerWorker


@pytest.fixture
def scheduler_worker(agent_config, sample_claim_set):
    runner = SimpleNamespace(
        is_idle=True,
        enqueue=Mock(),
    )
    state_handler = SimpleNamespace(
        agent=SimpleNamespace(is_healthy=True), runner=runner
    )
    client = SimpleNamespace(
        fetch_scenario_claim_set=AsyncMock(return_value=sample_claim_set),
        ack_scenario_claim_set=AsyncMock(),
    )
    telemetry = SimpleNamespace(emit_event=Mock())
    return ScenarioSchedulerWorker(
        config=agent_config,
        state_handler=state_handler,
        telemetry=telemetry,
        shutdown_event=asyncio.Event(),
        client=client,
    )


@pytest.mark.asyncio
async def test_should_execute_requires_healthy_idle_state(scheduler_worker):
    assert await scheduler_worker.should_execute() is True
    scheduler_worker.state_handler.agent.is_healthy = False
    assert await scheduler_worker.should_execute() is False


@pytest.mark.asyncio
async def test_run_iteration_fetches_and_acks_claim_set(
    scheduler_worker, sample_claim_set
):
    result = await scheduler_worker.run_iteration()

    assert result == {"claim_set": sample_claim_set}
    scheduler_worker.client.ack_scenario_claim_set.assert_awaited_once_with(
        sample_claim_set.id
    )


@pytest.mark.asyncio
async def test_handle_iteration_success_enqueues_and_emits_events(
    scheduler_worker, sample_claim_set
):
    await scheduler_worker.handle_iteration_success({"claim_set": sample_claim_set})

    scheduler_worker.state_handler.runner.enqueue.assert_called_once_with(
        sample_claim_set
    )
    emitted_event = scheduler_worker.telemetry.emit_event.call_args.kwargs["event"]
    assert emitted_event.event_name == EventEnum.SCENARIO_QUEUED


@pytest.mark.asyncio
async def test_handle_iteration_error_downgrades_api_conflict(scheduler_worker):
    error = APIRequestError("claimed", status_code=500)

    await scheduler_worker.handle_iteration_error({}, error)

    assert error.status_code == 409


@pytest.mark.asyncio
async def test_handle_iteration_error_logs_other_failures(scheduler_worker):
    error = RuntimeError("boom")

    await scheduler_worker.handle_iteration_error({}, error)
