import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from agent.core.lifecycle import LifecycleManager


def test_register_signal_handlers_uses_asyncio_loop():
    loop = Mock()
    manager = LifecycleManager(worker_manager=Mock(), shutdown_event=asyncio.Event())

    with patch("agent.core.lifecycle.asyncio.get_running_loop", return_value=loop):
        manager.register_signal_handlers()

    assert loop.add_signal_handler.call_count == len(manager.SHUTDOWN_SIGNALS)


def test_register_signal_handlers_falls_back_to_signal_module():
    loop = Mock()
    loop.add_signal_handler.side_effect = NotImplementedError
    manager = LifecycleManager(worker_manager=Mock(), shutdown_event=asyncio.Event())

    with (
        patch("agent.core.lifecycle.asyncio.get_running_loop", return_value=loop),
        patch("agent.core.lifecycle.signal.signal") as signal_mock,
    ):
        manager.register_signal_handlers()

    assert signal_mock.call_count == len(manager.SHUTDOWN_SIGNALS)


@pytest.mark.asyncio
async def test_run_starts_workers_waits_and_shuts_down():
    shutdown_event = asyncio.Event()
    shutdown_event.set()
    worker_manager = Mock(start_all_workers=Mock(), shutdown_all_workers=AsyncMock())
    manager = LifecycleManager(
        worker_manager=worker_manager, shutdown_event=shutdown_event
    )

    with patch.object(manager, "register_signal_handlers") as register_mock:
        await manager.run()

    register_mock.assert_called_once()
    worker_manager.start_all_workers.assert_called_once()
    worker_manager.shutdown_all_workers.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_shuts_down_when_cancelled():
    shutdown_event = asyncio.Event()
    shutdown_event.wait = AsyncMock(side_effect=asyncio.CancelledError())
    worker_manager = Mock(start_all_workers=Mock(), shutdown_all_workers=AsyncMock())
    manager = LifecycleManager(
        worker_manager=worker_manager, shutdown_event=shutdown_event
    )

    with patch.object(manager, "register_signal_handlers"):
        await manager.run()

    worker_manager.shutdown_all_workers.assert_awaited_once()
