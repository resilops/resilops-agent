import asyncio

from agent.clients.control_plane import ControlPlaneClient
from agent.clients.token import AuthServiceClient
from agent.constants import DISCOVERY_K8S_LEASE_NAME
from agent.core.leader import KubernetesLeaderElection
from agent.core.lifecycle import LifecycleManager
from agent.core.manager import WorkerManager
from agent.handlers.runner import ScenarioRunner
from agent.handlers.snapshot import SnapshotHandler
from agent.handlers.state import AgentStateHandler
from agent.handlers.telemetry import AgentTelemetry
from agent.logging import setup_logging
from agent.schemas.config import AgentConfig
from agent.workers.heartbeat import HeartbeatWorker
from agent.workers.runner import ScenarioRunnerWorker
from agent.workers.scheduler import ScenarioSchedulerWorker
from agent.workers.snapshot import SnapshotWorker


async def main() -> None:
    """Build the agent runtime and start the lifecycle manager."""

    # Setup logging
    setup_logging()

    shutdown_event = asyncio.Event()

    # Load agent configuration from environment
    config = AgentConfig()  # noqa

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
        HeartbeatWorker(
            config=config,
            state_handler=state_handler,
            telemetry=telemetry,
            shutdown_event=shutdown_event,
            client=control_plane_client,
        ),
        ScenarioSchedulerWorker(
            config=config,
            state_handler=state_handler,
            telemetry=telemetry,
            shutdown_event=shutdown_event,
            client=control_plane_client,
        ),
        ScenarioRunnerWorker(
            config=config,
            state_handler=state_handler,
            telemetry=telemetry,
            runner=ScenarioRunner(client=control_plane_client, telemetry=telemetry),
            shutdown_event=shutdown_event,
        ),
        SnapshotWorker(
            config=config,
            state_handler=state_handler,
            telemetry=telemetry,
            snapshot_handler=SnapshotHandler(
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
