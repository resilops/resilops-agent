import asyncio

import pytest

from agent.core.worker import PeriodicWorker


class DemoWorker(PeriodicWorker):
    WORKER_NAME = "demo"

    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self._should_execute = True
        self.success_results = []
        self.error_results = []
        self.run_result = {}

    def execution_interval(self) -> int:
        return 1

    async def should_execute(self) -> bool:
        return self._should_execute

    async def run_iteration(self):
        if isinstance(self.run_result, Exception):
            raise self.run_result
        return self.run_result

    async def handle_iteration_success(self, result):
        self.success_results.append(result)

    async def handle_iteration_error(self, result, error):
        self.error_results.append((result, error))


@pytest.mark.asyncio
async def test_execute_safely_handles_success_and_error():
    worker = DemoWorker()
    worker.run_result = {"ok": True}
    await worker._execute_safely()

    error = RuntimeError("boom")
    error.context = {"source": "ctx"}
    worker.run_result = error
    await worker._execute_safely()

    assert worker.success_results == [{"ok": True}]
    assert worker.error_results[0][0] == {"source": "ctx"}
    assert worker.error_results[0][1] is error


@pytest.mark.asyncio
async def test_run_continuously_executes_until_shutdown():
    worker = DemoWorker()
    calls = []

    async def fake_sleep():
        calls.append("sleep")
        worker.shutdown_event.set()

    worker._sleep_until_next_iteration = fake_sleep
    worker.run_result = {"done": True}

    await worker.run_continuously()

    assert calls == ["sleep"]
    assert worker.success_results == []


@pytest.mark.asyncio
async def test_run_continuously_executes_iteration_when_allowed():
    worker = DemoWorker()
    iteration_count = 0

    async def fake_sleep():
        nonlocal iteration_count
        iteration_count += 1
        if iteration_count > 1:
            worker.shutdown_event.set()

    worker._sleep_until_next_iteration = fake_sleep
    worker.run_result = {"done": True}

    await worker.run_continuously()

    assert worker.success_results == [{"done": True}]
