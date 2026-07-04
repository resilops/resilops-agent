import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from agent.core.manager import WorkerManager


def test_start_all_workers_registers_created_tasks():
    worker = SimpleNamespace(WORKER_NAME="w1", run_continuously=AsyncMock())
    agent = SimpleNamespace(register_workers=Mock())
    manager = WorkerManager(
        state_handler=SimpleNamespace(agent=agent),
        workers=[worker],
        shutdown_event=asyncio.Event(),
    )

    created_tasks = []

    def fake_create_task(coro, name):
        coro.close()
        task = Mock()
        task.get_name.return_value = name
        created_tasks.append(task)
        return task

    with patch("agent.core.manager.asyncio.create_task", side_effect=fake_create_task):
        manager.start_all_workers()

    agent.register_workers.assert_called_once_with(created_tasks)


def test_cancel_worker_tasks_cancels_each_task():
    task1 = Mock()
    task2 = Mock()

    WorkerManager._cancel_worker_tasks([task1, task2])

    task1.cancel.assert_called_once()
    task2.cancel.assert_called_once()


def test_log_shutdown_errors_logs_only_exceptions():
    task = Mock()
    task.get_name.return_value = "worker-1"

    with patch("agent.core.manager.logger.error") as error_mock:
        WorkerManager._log_shutdown_errors([task], [RuntimeError("boom")])
        WorkerManager._log_shutdown_errors([task], [None])

    error_mock.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_all_workers_sets_event_and_waits_for_tasks():
    task = Mock()
    manager = WorkerManager(
        state_handler=SimpleNamespace(agent=SimpleNamespace(current_workers=[task])),
        workers=[],
        shutdown_event=asyncio.Event(),
    )

    with (
        patch.object(manager, "_cancel_worker_tasks") as cancel_mock,
        patch(
            "agent.core.manager.asyncio.gather",
            new=AsyncMock(return_value=[None]),
        ) as gather_mock,
        patch.object(manager, "_log_shutdown_errors") as log_mock,
    ):
        await manager.shutdown_all_workers()

    assert manager.shutdown_event.is_set()
    cancel_mock.assert_called_once_with([task])
    gather_mock.assert_awaited_once()
    log_mock.assert_called_once_with([task], [None])
