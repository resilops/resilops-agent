import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from agent.workers.heartbeat import HeartbeatWorker


@pytest.fixture
def heartbeat_worker(agent_config):
    state_handler = SimpleNamespace(agent=SimpleNamespace(set_health=AsyncMock()))
    state_handler.agent.set_health = SimpleNamespace(__call__=None)
    state_handler.agent.set_health = lambda healthy: setattr(
        state_handler.agent, "healthy", healthy
    )
    return HeartbeatWorker(
        config=agent_config,
        state_handler=state_handler,
        telemetry=SimpleNamespace(),
        shutdown_event=asyncio.Event(),
        client=SimpleNamespace(send_heartbeat=AsyncMock()),
    )


@pytest.mark.asyncio
async def test_run_iteration_sends_heartbeat(heartbeat_worker):
    await heartbeat_worker.run_iteration()

    heartbeat_worker.client.send_heartbeat.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_iteration_success_and_error(heartbeat_worker):
    await heartbeat_worker.handle_iteration_success({})
    assert heartbeat_worker.state_handler.agent.healthy is True

    await heartbeat_worker.handle_iteration_error({}, RuntimeError("boom"))
    assert heartbeat_worker.state_handler.agent.healthy is False
