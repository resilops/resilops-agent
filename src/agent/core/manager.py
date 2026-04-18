import asyncio
import logging
from typing import Iterable, List

from agent.core.worker import PeriodicWorker
from agent.handlers.state import AgentStateHandler

logger = logging.getLogger(__name__)


class WorkerManager:
    """Start, track, and stop background worker tasks for the agent."""

    def __init__(
        self,
        state_handler: AgentStateHandler,
        workers: Iterable[PeriodicWorker],
        shutdown_event: asyncio.Event,
    ):
        """Create a worker manager for the supplied worker set."""
        self.state_handler = state_handler
        self.workers: List[PeriodicWorker] = list(workers)
        self.shutdown_event = shutdown_event

    def start_all_workers(self) -> None:
        """Create tasks for all workers and register them in agent state."""
        worker_tasks = [
            asyncio.create_task(worker.run_continuously(), name=worker.WORKER_NAME)
            for worker in self.workers
        ]
        self.state_handler.agent.register_workers(worker_tasks)
        logger.info(
            "Started %d background workers",
            len(self.workers),
            extra={"workers": [worker.WORKER_NAME for worker in self.workers]},
        )

    @staticmethod
    def _cancel_worker_tasks(worker_tasks: List[asyncio.Task]) -> None:
        """Cancel every tracked worker task."""
        for worker_task in worker_tasks:
            worker_task.cancel()

    @staticmethod
    def _log_shutdown_errors(
        worker_tasks: List[asyncio.Task], results: List[object]
    ) -> None:
        """Log worker exceptions raised during shutdown."""
        for worker_task, result in zip(worker_tasks, results):
            if isinstance(result, Exception):
                logger.error(
                    "Worker raised an exception during shutdown",
                    extra={"worker": worker_task.get_name()},
                    exc_info=(type(result), result, result.__traceback__),
                )

    async def shutdown_all_workers(self) -> None:
        """Cancel running workers and wait for them to finish."""
        logger.info("Initiating shutdown of background workers")
        self.shutdown_event.set()
        worker_tasks = self.state_handler.agent.current_workers

        self._cancel_worker_tasks(worker_tasks)

        results = await asyncio.gather(*worker_tasks, return_exceptions=True)
        self._log_shutdown_errors(worker_tasks, results)

        logger.info("All background workers have been shut down")
