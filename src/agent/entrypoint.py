import asyncio

from agent.clients.control_plane import ControlPlaneClient
from agent.clients.token import AuthServiceClient
from agent.constants import DISCOVERY_K8S_LEASE_NAME
from agent.core.leader import KubernetesLeaderElection
from agent.core.lifecycle import LifecycleManager
from agent.core.manager import WorkerManager
from agent.handlers.runner import ResiliencyScenarioRunner
from agent.handlers.snapshot import NamespaceSnapshotHandler
from agent.handlers.state import AgentStateHandler
from agent.handlers.telemetry import AgentTelemetry
from agent.logging import setup_logging
from agent.schemas.config import AgentConfigModel
from agent.workers.heartbeat import HealthMonitorWorker
from agent.workers.runner import ResiliencyScenarioRunnerWorker
from agent.workers.scheduler import ResiliencyScenarioSchedulerWorker
from agent.workers.snapshot import NamespacesSnapshotWorker


async def main() -> None:
    """Build the agent runtime and start the lifecycle manager."""

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

    leader_election = KubernetesLeaderElection(
        lease_name=DISCOVERY_K8S_LEASE_NAME,
        namespace=config.namespace,
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
        ResiliencyScenarioSchedulerWorker(
            config=config,
            state_handler=state_handler,
            telemetry=telemetry,
            shutdown_event=shutdown_event,
            client=control_plane_client,
        ),
        ResiliencyScenarioRunnerWorker(
            config=config,
            state_handler=state_handler,
            telemetry=telemetry,
            runner=ResiliencyScenarioRunner(
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
    """Run the async entrypoint from the package console script."""
    asyncio.run(main())
