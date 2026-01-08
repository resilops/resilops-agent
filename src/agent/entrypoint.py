import asyncio

from agent.clients.control_plane import ControlPlaneClient
from agent.core.lifecycle import LifecycleManager
from agent.core.worker import WorkerManager
from agent.handlers.event import EventHandler
from agent.handlers.resiliency import ResiliencyPlanExecutionHandler
from agent.handlers.state import StateHandler
from agent.logging import setup_logging
from agent.schemas.config import AgentConfigModel
from agent.workers.executor import ResiliencyPlanExecutorWorker
from agent.workers.fetcher import ResiliencyPlanFetcherWorker
from agent.workers.heartbeat import HealthMonitorWorker


async def main() -> None:
    """
    Main entry point for the Resiliency agent.
    Sets up configuration, state, workers, and lifecycle manager, then runs.
    """

    # Setup logging
    setup_logging()

    shutdown_event = asyncio.Event()

    # Load agent configuration from environment
    config = AgentConfigModel()

    # Initialize API client
    control_plane_client = ControlPlaneClient(config)

    # Initialize agent runtime state
    state = StateHandler()

    # Initialise event handler
    event = EventHandler()

    # Create background workers
    workers = (
        HealthMonitorWorker(
            config=config,
            state=state,
            event=event,
            shutdown_event=shutdown_event,
            client=control_plane_client,
        ),
        ResiliencyPlanFetcherWorker(
            config=config,
            state=state,
            event=event,
            shutdown_event=shutdown_event,
            client=control_plane_client,
        ),
        ResiliencyPlanExecutorWorker(
            config=config,
            state=state,
            event=event,
            executor=ResiliencyPlanExecutionHandler(client=control_plane_client),
            shutdown_event=shutdown_event,
        ),
    )

    # Initialize worker manager and lifecycle manager
    worker_manager = WorkerManager(
        state=state, workers=workers, shutdown_event=shutdown_event
    )
    lifecycle_manager = LifecycleManager(
        state=state, worker_manager=worker_manager, shutdown_event=shutdown_event
    )

    # Run the agent lifecycle
    await lifecycle_manager.run()


def run() -> None:
    """
    Synchronous wrapper for the async main function.
    This is what gets called from the Poetry script entry point.
    """
    asyncio.run(main())
