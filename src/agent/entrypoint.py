import asyncio

from agent.clients.control_plane import ControlPlaneClient
from agent.clients.token import AuthServiceClient
from agent.constants import DISCOVERY_k8_LEASE_NAME
from agent.core.leader import KubernetesLeaderElection
from agent.core.lifecycle import LifecycleManager
from agent.core.manager import WorkerManager
from agent.handlers.runner import ResiliencySuiteRunner
from agent.handlers.snapshot import NamespaceSnapshotHandler
from agent.handlers.state import AgentStateHandler
from agent.handlers.telemetry import AgentTelemetry
from agent.logging import setup_logging
from agent.schemas.config import AgentConfigModel
from agent.workers.heartbeat import HealthMonitorWorker
from agent.workers.runner import ResiliencySuiteRunnerWorker
from agent.workers.scheduler import ResiliencySuiteSchedulerWorker
from agent.workers.snapshot import NamespacesSnapshotWorker


async def main() -> None:
    """
    Main entry point for the Resiliency agent.
    Sets up configuration, state, workers, and lifecycle manager, then runs.
    """

    # Setup logging
    setup_logging()

    shutdown_event = asyncio.Event()

    # Load agent configuration from environment
    config = AgentConfigModel()  # noqa

    # Initialize API client
    control_plane_client = ControlPlaneClient(
        config=config, auth_service=AuthServiceClient(config=config)
    )

    # Initialize agent runtime state
    state_handler = AgentStateHandler()

    # Initialize event handler
    telemetry = AgentTelemetry()

    # Kubernetes lease coordinator
    leader_election = KubernetesLeaderElection(
        lease_name=DISCOVERY_k8_LEASE_NAME, namespace=config.namespace
    )

    # Create background workers
    workers = [
        HealthMonitorWorker(
            config=config,
            state_handler=state_handler,
            telemetry=telemetry,
            shutdown_event=shutdown_event,
            client=control_plane_client,
        ),
        ResiliencySuiteSchedulerWorker(
            config=config,
            state_handler=state_handler,
            telemetry=telemetry,
            shutdown_event=shutdown_event,
            client=control_plane_client,
        ),
        ResiliencySuiteRunnerWorker(
            config=config,
            state_handler=state_handler,
            telemetry=telemetry,
            runner=ResiliencySuiteRunner(
                client=control_plane_client, telemetry=telemetry
            ),
            shutdown_event=shutdown_event,
        ),
        NamespacesSnapshotWorker(
            config=config,
            state_handler=state_handler,
            telemetry=telemetry,
            snapshot_handler=NamespaceSnapshotHandler(
                config=config,
                client=control_plane_client,
                leader_election=leader_election,
            ),
            leader_election=leader_election,
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
