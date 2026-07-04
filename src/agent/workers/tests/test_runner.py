import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from agent.workers.runner import ScenarioRunnerWorker


@pytest.fixture
def runner_state(sample_claim_set):
    return SimpleNamespace(
        is_queued=True,
        is_idle=False,
        current_claim_set=sample_claim_set,
        mark_running=AsyncMock(),
        reset_to_idle=AsyncMock(),
    )


@pytest.fixture
def runner_worker(agent_config, runner_state):
    runner = SimpleNamespace(
        is_queued=True,
        is_idle=False,
        current_claim_set=runner_state.current_claim_set,
    )
    runner.mark_running = lambda: setattr(runner, "marked", True)
    runner.reset_to_idle = lambda: setattr(runner, "reset", True)
    state_handler = SimpleNamespace(
        agent=SimpleNamespace(is_healthy=True), runner=runner
    )
    return ScenarioRunnerWorker(
        config=agent_config,
        state_handler=state_handler,
        telemetry=SimpleNamespace(),
        runner=SimpleNamespace(execute_claim_set=AsyncMock()),
        shutdown_event=asyncio.Event(),
    )


@pytest.mark.asyncio
async def test_should_execute_requires_healthy_agent_and_queued_claim_set(
    runner_worker,
):
    assert await runner_worker.should_execute() is True

    runner_worker.state_handler.agent.is_healthy = False
    assert await runner_worker.should_execute() is False


@pytest.mark.asyncio
async def test_run_iteration_marks_running_and_executes_claim_set(runner_worker):
    result = await runner_worker.run_iteration()

    assert runner_worker.state_handler.runner.marked is True
    assert result["claim_set"] == runner_worker.state_handler.runner.current_claim_set
    runner_worker.runner.execute_claim_set.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_iteration_success_and_error_reset_state(runner_worker):
    await runner_worker.handle_iteration_success({})
    assert runner_worker.state_handler.runner.reset is True

    runner_worker.state_handler.runner.reset = False
    await runner_worker.handle_iteration_error({}, RuntimeError("boom"))
    assert runner_worker.state_handler.runner.reset is True
