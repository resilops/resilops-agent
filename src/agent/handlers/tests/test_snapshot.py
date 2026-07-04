from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from agent.exceptions import NotLeaderError
from agent.handlers.snapshot import SnapshotHandler


def test_chunked_splits_batches():
    result = list(SnapshotHandler._chunked(["a", "b", "c", "d", "e"], 2))

    assert result == [["a", "b"], ["c", "d"], ["e"]]


def test_chunked_rejects_non_positive_batch_sizes():
    with pytest.raises(ValueError, match="greater than 0"):
        list(SnapshotHandler._chunked(["a"], 0))


@pytest.mark.asyncio
async def test_ensure_leadership_raises_when_not_leader(agent_config):
    handler = SnapshotHandler(
        config=agent_config,
        client=SimpleNamespace(),
        leader_election=SimpleNamespace(acquire_or_renew_lease=lambda: False),
    )

    with pytest.raises(NotLeaderError):
        await handler._ensure_leadership()


@pytest.mark.asyncio
async def test_capture_and_publish_snapshot(agent_config):
    publish_cluster_snapshot = AsyncMock()
    handler = SnapshotHandler(
        config=agent_config,
        client=SimpleNamespace(publish_cluster_snapshot=publish_cluster_snapshot),
        leader_election=SimpleNamespace(acquire_or_renew_lease=lambda: True),
    )
    sync_id = uuid4()

    with (
        patch.object(handler, "_ensure_leadership", new=AsyncMock()) as ensure_mock,
        patch.object(handler, "_sleep_with_jitter", new=AsyncMock()) as sleep_mock,
        patch(
            "agent.handlers.snapshot.random.sample",
            return_value=["team-a", "team-b"],
        ),
        patch("agent.handlers.snapshot.uuid.uuid4", return_value=sync_id),
        patch(
            "agent.handlers.snapshot.discover_namespaces",
            return_value=["ns-state"],
        ),
        patch(
            "agent.handlers.snapshot.ClusterSnapshot",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs),
        ),
    ):
        await handler.capture_and_publish_snapshot()

    assert ensure_mock.await_count == 2
    publish_cluster_snapshot.assert_awaited_once()
    payload = publish_cluster_snapshot.await_args.kwargs["payload"]
    assert str(payload.sync_uuid) == str(sync_id)
    assert payload.namespaces == ["ns-state"]
    sleep_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_capture_and_publish_snapshot_attaches_sync_uuid_on_failure(agent_config):
    publish_cluster_snapshot = AsyncMock()
    handler = SnapshotHandler(
        config=agent_config,
        client=SimpleNamespace(publish_cluster_snapshot=publish_cluster_snapshot),
        leader_election=SimpleNamespace(acquire_or_renew_lease=lambda: True),
    )
    sync_id = uuid4()

    with (
        patch.object(handler, "_ensure_leadership", new=AsyncMock()),
        patch("agent.handlers.snapshot.random.sample", return_value=["team-a"]),
        patch("agent.handlers.snapshot.uuid.uuid4", return_value=sync_id),
        patch(
            "agent.handlers.snapshot.discover_namespaces",
            side_effect=ValueError("broken"),
        ),
    ):
        with pytest.raises(ValueError) as exc_info:
            await handler.capture_and_publish_snapshot()

    assert exc_info.value.result == {"sync_uuid": sync_id}
