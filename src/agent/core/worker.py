import asyncio
import logging
from typing import Iterable, List

from agent.models.agent import AgentStateModel
from agent.workers.base import PeriodicWorker

logger = logging.getLogger(__name__)


class WorkerManager:
    """
    Manages the lifecycle of background workers for the agent.

    Responsibilities:
    - Start all workers and track them
    - Gracefully stop/cancel workers on shutdown
    - Integrate with the agent's runtime state
    """

    def __init__(
        self,
        agent: AgentStateModel,
        workers: Iterable[PeriodicWorker],
        shutdown_event: asyncio.Event,
    ):
        """
        Initialize the worker manager.

        Args:
            agent: The agent's runtime state object.
            workers: Iterable of periodic workers to manage.
            shutdown_event: Asyncio event used to signal shutdown.
        """
        self.agent = agent
        self.workers: List[PeriodicWorker] = list(workers)
        self.shutdown_event = shutdown_event

    def start_all_workers(self) -> None:
        """
        Start all background workers concurrently and track them in the agent state.

        Each worker is wrapped as an asyncio.Task so it can run concurrently.
        """
        worker_tasks = [
            asyncio.create_task(worker.run_continuously(), name=worker.WORKER_NAME)
            for worker in self.workers
        ]
        self.agent.set_running_tasks(worker_tasks)
        logger.info(
            "Started %d background workers",
            len(worker_tasks),
            extra={"workers": self.workers},
        )

    async def shutdown_all_workers(self) -> None:
        """
        Cancel all running workers and wait for their termination.

        This ensures a graceful shutdown and prevents dangling workers.
        """
        logger.info("Initiating shutdown of background workers")
        self.shutdown_event.set()  # Signal all workers to stop

        for worker_task in self.agent.running_tasks:
            worker_task.cancel()  # Cancel each asyncio task

        # Wait for all worker tasks to complete and collect exceptions
        results = await asyncio.gather(
            *self.agent.running_tasks, return_exceptions=True
        )

        # Log exceptions, if any
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.exception(
                    "Worker raised an exception during shutdown",
                    extra={"id": id, "result": result},
                )

        logger.info("All background workers have been shut down")
