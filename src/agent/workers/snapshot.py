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
    """Run namespace discovery snapshots when this instance is leader."""

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
        """Create the namespace snapshot worker."""
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

    def _emit_snapshot_event(
        self,
        event_name: EventEnum,
        *,
        sync_uuid: Optional[str],
        error: Optional[Exception] = None,
    ) -> None:
        """Emit a snapshot-related telemetry event."""
        data = {"sync_uuid": str(sync_uuid)}
        if error is not None:
            data["error"] = str(error)

        self.telemetry.emit_event(
            event=EventPayload(
                event_name=event_name,
                data=data,
                error=None if error is None else error.__class__.__name__,
            ),
        )

    def execution_interval(self) -> int:
        """Return a fast retry interval until the first successful snapshot."""
        if (
            not self._has_succeeded_once
            and self._startup_retry_attempts < self.STARTUP_RETRY_LIMIT
        ):
            self._startup_retry_attempts += 1
            return self.STARTUP_RETRY_INTERVAL
        return self.config.namespace_snapshot_interval

    async def should_execute(self) -> bool:
        """Execute only when the agent is healthy and leadership is held."""
        if not self.state_handler.agent.is_healthy:
            return False

        return await asyncio.to_thread(self.leader_election.acquire_or_renew_lease)

    async def run_iteration(self) -> Optional[Dict[str, str]]:
        """Run a snapshot iteration and return the sync UUID in the context."""
        sync_id: uuid.UUID = await self.snapshot_handler.capture_and_publish_snapshot()
        return {"sync_uuid": str(sync_id)}

    async def handle_iteration_success(self, context: Dict[str, Any]) -> None:
        """Mark startup complete and emit a successful discovery event."""
        self._has_succeeded_once = True
        sync_uuid = context.get("sync_uuid")
        self._emit_snapshot_event(EventEnum.DISCOVERY_SUCCESS, sync_uuid=sync_uuid)

    async def handle_iteration_error(
        self,
        context: Dict[str, Any],
        error: Exception,
    ) -> None:
        """Emit failure telemetry unless the worker simply lost leadership."""
        if isinstance(error, NotLeaderError):
            logger.debug("Not leader, so skipping snapshot execution.")
            return

        sync_uuid = context.get("sync_uuid")
        self._emit_snapshot_event(
            EventEnum.DISCOVERY_FAILED,
            sync_uuid=sync_uuid,
            error=error,
        )
