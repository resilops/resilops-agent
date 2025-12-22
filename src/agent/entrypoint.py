import asyncio

from agent.clients.control_plane import ControlPlaneClient
from agent.core.lifecycle import LifecycleManager
from agent.core.worker import WorkerManager
from agent.logging import setup_logging
from agent.models.agent import AgentStateModel
from agent.models.config import AgentConfigModel
from agent.workers.executor import PlanExecutorWorker
from agent.workers.fetcher import PlanFetcherWorker
from agent.workers.heartbeat import HealthMonitorWorker


async def main() -> None:
    """
    Main entry point for the Fault agent.
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
    agent = AgentStateModel()

    # Create background workers
    workers = (
        HealthMonitorWorker(
            config=config,
            agent=agent,
            shutdown_event=shutdown_event,
            client=control_plane_client,
        ),
        PlanFetcherWorker(
            config=config,
            agent=agent,
            shutdown_event=shutdown_event,
            client=control_plane_client,
        ),
        PlanExecutorWorker(config=config, agent=agent, shutdown_event=shutdown_event),
    )

    # Initialize worker manager and lifecycle manager
    worker_manager = WorkerManager(
        agent=agent, workers=workers, shutdown_event=shutdown_event
    )
    lifecycle_manager = LifecycleManager(
        agent=agent, worker_manager=worker_manager, shutdown_event=shutdown_event
    )

    # Run the agent lifecycle
    await lifecycle_manager.run()


def run() -> None:
    """
    Synchronous wrapper for the async main function.
    This is what gets called from the Poetry script entry point.
    """
    asyncio.run(main())
