import asyncio
import logging
import uuid
from typing import Any, Dict, Optional

from agent.core.leader import KubernetesLeaderElection
from agent.core.worker import PeriodicWorker
from agent.exceptions import NotLeaderError
from agent.handlers.snapshot import NamespaceSnapshotHandler
from agent.handlers.state import AgentStateHandler
from agent.handlers.telemetry import AgentTelemetry
from agent.schemas.config import AgentConfigModel
from agent.schemas.event import EventEnum, EventPayload

logger = logging.getLogger(__name__)


class NamespacesSnapshotWorker(PeriodicWorker):
    """
    Periodic worker responsible for discovering Kubernetes namespaces and
    sending their state snapshots to the control plane.

    This worker runs at a configured interval and triggers the snapshot
    process only when the agent is healthy and the runner is idle. It also
    emits telemetry events for success and failure of each execution cycle.
    """

    WORKER_NAME: str = "namespaces_snapshot"
    STARTUP_RETRY_INTERVAL = 20
    STARTUP_RETRY_LIMIT = 5

    def __init__(
        self,
        config: AgentConfigModel,
        state_handler: AgentStateHandler,
        telemetry: AgentTelemetry,
        shutdown_event: asyncio.Event,
        snapshot_handler: NamespaceSnapshotHandler,
        leader_election: KubernetesLeaderElection,
    ):
        """
        Initialize the NamespacesSnapshotWorker.

        Args:
            config: Agent configuration model.
            state_handler: Handler providing agent and runner state.
            telemetry: Telemetry client for emitting events.
            shutdown_event: Async event used to signal worker shutdown.
            snapshot_handler: Handler responsible for performing namespace snapshots.
            leader_election: KubernetesLeaderElection instance.
        """
        super().__init__(
            config,
            state_handler,
            telemetry,
            shutdown_event,
        )
        self.snapshot_handler = snapshot_handler
        self.leader_election = leader_election
        self._startup_retry_attempts: int = 0
        self._has_succeeded_once = False

    def execution_interval(self) -> int:
        """
        Return the current sleep interval.

        Before the first successful execution, retry more frequently for a
        limited number of attempts. After that, fall back to the normal
        execution interval.
        """
        if (
            not self._has_succeeded_once
            and self._startup_retry_attempts < self.STARTUP_RETRY_LIMIT
        ):
            self._startup_retry_attempts += 1
            return self.STARTUP_RETRY_INTERVAL
        return self.config.namespace_snapshot_interval

    async def should_execute(self) -> bool:
        """
        Determine whether the worker should execute in the current cycle.

        The worker executes only when:
        - the agent is healthy
        - this instance successfully acquires or renews the leader lease

        Returns:
            True if execution should proceed, otherwise False.
        """
        if not self.state_handler.agent.is_healthy:
            return False

        return await asyncio.to_thread(self.leader_election.try_acquire_or_renew)

    async def execute_iteration(self) -> Optional[Dict[str, str]]:
        """
        Execute a single snapshot iteration.

        Triggers the namespace snapshot process and returns a context
        containing the generated sync UUID.

        Returns:
            A dictionary containing the sync UUID for this snapshot cycle.
        """
        sync_id: uuid.UUID = await self.snapshot_handler.snapshot()
        return {"sync_uuid": str(sync_id)}

    async def on_execution_success(self, context: Dict[str, Any]) -> None:
        """
        Handle successful execution of a snapshot iteration.

        Emits a telemetry event indicating successful namespace discovery.

        Args:
            context: Execution context containing metadata such as sync UUID.
        """
        self._has_succeeded_once = True
        sync_uuid = context.get("sync_uuid")
        self.telemetry.emit_event(
            event=EventPayload(
                event_name=EventEnum.DISCOVERY_SUCCESS,
                data={"sync_uuid": str(sync_uuid)},
            ),
        )

    async def on_execution_error(
        self,
        context: Dict[str, Any],
        error: Exception,
    ) -> None:
        """
        Handle errors during snapshot execution.

        Emits a telemetry event indicating failure, including error details.

        Args:
            context: Execution context containing metadata such as sync UUID.
            error: Exception raised during execution.
        """
        if isinstance(error, NotLeaderError):
            logger.debug("Not leader, so skipping snapshot execution.")
            return

        sync_uuid = context.get("sync_uuid")
        self.telemetry.emit_event(
            event=EventPayload(
                event_name=EventEnum.DISCOVERY_FAILED,
                data={"sync_uuid": str(sync_uuid), "error": str(error)},
                error=error.__class__.__name__,
            ),
        )
