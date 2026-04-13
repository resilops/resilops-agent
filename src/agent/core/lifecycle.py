import asyncio
import logging
import signal

from agent.core.manager import WorkerManager

logger = logging.getLogger(__name__)


class LifecycleManager:
    """Coordinate startup, signal handling, and shutdown for the agent."""

    SHUTDOWN_SIGNALS = (signal.SIGINT, signal.SIGTERM)

    def __init__(
        self,
        worker_manager: WorkerManager,
        shutdown_event: asyncio.Event,
    ):
        """Create the lifecycle manager."""
        self.worker_manager = worker_manager
        self.shutdown_event = shutdown_event

    def register_signal_handlers(self) -> None:
        """Register shutdown handlers for supported process signals."""
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
        """Start workers, wait for shutdown, then stop workers gracefully."""
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
        """Stop managed workers and finish shutdown."""
        logger.info("Resiliency agent initiating shutdown")
        await self.worker_manager.shutdown_all_workers()
        logger.info("Shutdown complete")
