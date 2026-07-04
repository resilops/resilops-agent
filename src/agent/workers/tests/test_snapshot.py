import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from agent.exceptions import NotLeaderError
from agent.schemas.event import EventEnum
from agent.workers.snapshot import SnapshotWorker


@pytest.fixture
def snapshot_worker(agent_config):
    telemetry = SimpleNamespace(emit_event=Mock())
    return SnapshotWorker(
        config=agent_config,
        state_handler=SimpleNamespace(agent=SimpleNamespace(is_healthy=True)),
        telemetry=telemetry,
        shutdown_event=asyncio.Event(),
        snapshot_handler=SimpleNamespace(
            capture_and_publish_snapshot=AsyncMock(return_value="sync-1")
        ),
        leader_election=SimpleNamespace(acquire_or_renew_lease=lambda: True),
    )


def test_execution_interval_uses_fast_startup_then_config(
    snapshot_worker, agent_config
):
    intervals = [snapshot_worker.execution_interval() for _ in range(6)]

    assert intervals[:5] == [snapshot_worker.STARTUP_RETRY_INTERVAL] * 5
    assert intervals[5] == agent_config.namespace_snapshot_interval


@pytest.mark.asyncio
async def test_should_execute_requires_health_and_leadership(snapshot_worker):
    assert await snapshot_worker.should_execute() is True

    snapshot_worker.state_handler.agent.is_healthy = False
    assert await snapshot_worker.should_execute() is False


@pytest.mark.asyncio
async def test_run_iteration_returns_sync_uuid(snapshot_worker):
    assert await snapshot_worker.run_iteration() == {"sync_uuid": "sync-1"}


@pytest.mark.asyncio
async def test_handle_iteration_success_and_error(snapshot_worker):
    await snapshot_worker.handle_iteration_success({"sync_uuid": "sync-1"})
    assert snapshot_worker._has_succeeded_once is True
    success_event = snapshot_worker.telemetry.emit_event.call_args.kwargs["event"]
    assert success_event.event_name == EventEnum.DISCOVERY_SUCCESS

    snapshot_worker.telemetry.emit_event.reset_mock()
    await snapshot_worker.handle_iteration_error(
        {"sync_uuid": "sync-2"}, RuntimeError("boom")
    )
    failure_event = snapshot_worker.telemetry.emit_event.call_args.kwargs["event"]
    assert failure_event.event_name == EventEnum.DISCOVERY_FAILED


@pytest.mark.asyncio
async def test_handle_iteration_error_ignores_not_leader(snapshot_worker):
    await snapshot_worker.handle_iteration_error({}, NotLeaderError("skip"))

    snapshot_worker.telemetry.emit_event.assert_not_called()
