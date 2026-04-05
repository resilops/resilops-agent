import asyncio
import logging
import random
import uuid
from typing import Iterable, List, Sequence

from reslib.k8s.discovery import discover_namespaces
from reslib.k8s.schema import DiscoveryNamespaceConfigSchema

from agent.clients.control_plane import ControlPlaneClient
from agent.core.leader import KubernetesLeaderElection
from agent.exceptions import NotLeaderError
from agent.schemas.config import AgentConfigModel
from agent.schemas.snapshot import ClusterSnapshotRequestModel

logger = logging.getLogger(__name__)


class NamespaceSnapshotHandler:
    """Handles batched namespace discovery and snapshot delivery."""

    DISCOVERY_BATCH_SIZE = 5
    DISCOVERY_MAX_JITTER_SECONDS = 5

    def __init__(
        self,
        config: AgentConfigModel,
        client: ControlPlaneClient,
        leader_election: KubernetesLeaderElection,
    ) -> None:
        self.config = config
        self.client = client
        self.leader_election = leader_election

    @staticmethod
    def _chunked(items: Sequence[str], batch_size: int) -> Iterable[List[str]]:
        """
        Split a sequence into fixed-size batches.

        Args:
            items: Items to split.
            batch_size: Maximum number of items per batch.

        Yields:
            Batches of items.
        """
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0")

        for index in range(0, len(items), batch_size):
            yield list(items[index : index + batch_size])

    async def _ensure_leadership(self) -> None:
        """
        Ensure this instance currently holds the Kubernetes leader lease.

        Raises:
            NotLeaderError: If this instance is not the current leader.
        """
        is_leader = await asyncio.to_thread(self.leader_election.try_acquire_or_renew)
        if not is_leader:
            raise NotLeaderError("Not a Kubernetes leader instance")

    async def _sleep_with_jitter(self) -> None:
        """Sleep for a random interval between discovery batches."""
        await asyncio.sleep(random.uniform(1, self.DISCOVERY_MAX_JITTER_SECONDS))

    async def snapshot(self) -> uuid.UUID:
        """
        Discover target namespaces in batches and send each batch snapshot to the
        control plane using the same sync UUID.

        Returns:
            The sync UUID associated with this snapshot run.

        Raises:
            NotLeaderError: If leadership is not held at execution time.
            Exception: Propagates discovery or control-plane errors.
        """
        await self._ensure_leadership()

        sync_uuid = uuid.uuid4()
        namespaces: List[str] = random.sample(
            self.config.target_namespaces,
            k=len(self.config.target_namespaces),
        )

        for namespace_batch in self._chunked(namespaces, self.DISCOVERY_BATCH_SIZE):
            await self._ensure_leadership()
            logger.info(
                "Snapshot discovery: %s for namespaces: %s", sync_uuid, namespace_batch
            )
            discovery_config = DiscoveryNamespaceConfigSchema(
                namespaces=namespace_batch,
            )
            try:
                namespace_states = await asyncio.wait_for(
                    asyncio.to_thread(discover_namespaces, discovery_config),
                    timeout=100,  # safety timeout
                )
                payload = ClusterSnapshotRequestModel(
                    sync_uuid=sync_uuid,
                    namespaces=namespace_states,
                )
                await self.client.cluster_snapshot(payload=payload)

            except Exception as exc:
                setattr(exc, "context", {"sync_uuid": sync_uuid})
                raise

            await self._sleep_with_jitter()

        return sync_uuid
