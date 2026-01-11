import asyncio
import logging
import signal

from agent.core.manager import WorkerManager

logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    Coordinates the lifecycle of a resiliency-agent.

    Responsibilities:
    - Register OS signal handlers for graceful shutdown
    - Start background workers via WorkerManager
    - Wait for a shutdown signal
    - Shutdown all running workers cleanly
    """

    SHUTDOWN_SIGNALS = (signal.SIGINT, signal.SIGTERM)

    def __init__(
        self,
        worker_manager: WorkerManager,
        shutdown_event: asyncio.Event,
    ):
        """
        Initialize the lifecycle manager.

        Args:
            worker_manager: Responsible for starting/stopping background workers.
            shutdown_event: Async event used to signal shutdown.
        """
        self.worker_manager = worker_manager
        self.shutdown_event = shutdown_event

    def register_signal_handlers(self) -> None:
        """
        Register OS signal handlers (SIGINT, SIGTERM) to trigger graceful shutdown.

        On platforms where `loop.add_signal_handler` is not supported (Windows),
        fallback to `signal.signal`.
        """
        loop = asyncio.get_running_loop()
        logger.info("Registering shutdown signal handlers")
        for sig in self.SHUTDOWN_SIGNALS:
            try:
                # Preferred for UNIX-like platforms
                loop.add_signal_handler(sig, self.shutdown_event.set)
            except NotImplementedError:
                # Fallback for Windows
                signal.signal(sig, lambda signum, frame: self.shutdown_event.set())

    async def run(self) -> None:
        """
        Start the agent lifecycle manager.

        - Registers signal handlers
        - Starts all background workers via worker manager
        - Waits for the shutdown event
        - Performs a graceful shutdown when triggered
        """
        self.register_signal_handlers()
        self.worker_manager.start_all_workers()
        logger.info("Resiliency agent started and running")

        try:
            await self.shutdown_event.wait()
        except asyncio.CancelledError:
            logger.info("Agent lifecycle manager was cancelled")
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """
        Shutdown the agent gracefully.

        - Stops all running workers via worker manager
        - Waits for worker completion and logs any exceptions
        - Logs completion of shutdown
        """
        logger.info("Resiliency agent initiating shutdown")
        await self.worker_manager.shutdown_all_workers()
        logger.info("Shutdown complete")
