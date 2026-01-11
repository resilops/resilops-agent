import asyncio

from agent.clients.control_plane import ControlPlaneClient
from agent.core.lifecycle import LifecycleManager
from agent.core.manager import WorkerManager
from agent.handlers.event import EventHandler
from agent.handlers.runner import ResiliencyPlanRunner
from agent.handlers.state import AgentStateHandler
from agent.logging import setup_logging
from agent.schemas.config import AgentConfigModel
from agent.workers.heartbeat import HealthMonitorWorker
from agent.workers.runner import ResiliencyPlanRunnerWorker
from agent.workers.scheduler import ResiliencyPlanSchedulerWorker


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
    state_handler = AgentStateHandler()

    # Initialise event handler
    event_handler = EventHandler()

    # Create background workers
    workers = [
        HealthMonitorWorker(
            config=config,
            state_handler=state_handler,
            event_handler=event_handler,
            shutdown_event=shutdown_event,
            client=control_plane_client,
        ),
        ResiliencyPlanSchedulerWorker(
            config=config,
            state_handler=state_handler,
            event_handler=event_handler,
            shutdown_event=shutdown_event,
            client=control_plane_client,
        ),
        ResiliencyPlanRunnerWorker(
            config=config,
            state_handler=state_handler,
            event_handler=event_handler,
            runner=ResiliencyPlanRunner(client=control_plane_client),
            shutdown_event=shutdown_event,
        ),
    ]

    # Initialize worker manager and lifecycle manager
    worker_manager = WorkerManager(
        state_handler=state_handler, workers=workers, shutdown_event=shutdown_event
    )
    lifecycle_manager = LifecycleManager(
        worker_manager=worker_manager, shutdown_event=shutdown_event
    )

    # Run the agent lifecycle
    await lifecycle_manager.run()


def run() -> None:
    """
    Synchronous wrapper for the async main function.
    This is what gets called from the Poetry script entry point.
    """
    asyncio.run(main())
