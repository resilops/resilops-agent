from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from agent.clients.control_plane import ControlPlaneClient
from agent.constants import AGENT_CLAIM_SET_ACK_PATH


@pytest.fixture
def auth_service():
    return SimpleNamespace(
        get_m2m_token=AsyncMock(return_value=SimpleNamespace(access_token="abc"))
    )


@pytest.fixture
def client(agent_config, auth_service):
    return ControlPlaneClient(agent_config, auth_service)


def test_host_uses_control_plane_setting(client, agent_config):
    assert client.host == agent_config.control_plane_api_host


@pytest.mark.asyncio
async def test_get_headers_uses_bearer_token(client, auth_service):
    headers = await client.get_headers()

    assert headers["Authorization"] == "Bearer abc"
    auth_service.get_m2m_token.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_heartbeat_serializes_payload(client, agent_config):
    response_model = object()

    with (
        patch.object(
            client, "request", new=AsyncMock(return_value={"health": "healthy"})
        ) as request_mock,
        patch(
            "agent.clients.control_plane.HeartbeatResponse",
            return_value=response_model,
        ) as response_cls,
    ):
        result = await client.send_heartbeat()

    assert result is response_model
    request_mock.assert_awaited_once()
    payload = request_mock.await_args.kwargs["json"]
    assert payload["version"] == agent_config.app_version
    assert payload["config_version"] == agent_config.config_version
    assert payload["reason"] is None
    response_cls.assert_called_once_with(**{"health": "healthy"})


@pytest.mark.asyncio
async def test_fetch_scenario_claim_set_returns_pending_claim_set(client):
    pending_claim_set = SimpleNamespace(status="pending")

    with (
        patch.object(
            client, "request", new=AsyncMock(return_value=[{"id": "claim-set"}])
        ),
        patch(
            "agent.clients.control_plane.ScenarioClaimSet",
            return_value=pending_claim_set,
        ) as claim_set_cls,
    ):
        result = await client.fetch_scenario_claim_set()

    assert result is pending_claim_set
    claim_set_cls.assert_called_once_with(**{"id": "claim-set"})


@pytest.mark.asyncio
async def test_fetch_scenario_claim_set_ignores_empty_and_non_pending(client):
    non_pending_claim_set = SimpleNamespace(status="acknowledged")

    with patch.object(client, "request", new=AsyncMock(return_value=[])):
        assert await client.fetch_scenario_claim_set() is None

    with (
        patch.object(
            client, "request", new=AsyncMock(return_value=[{"id": "claim-set"}])
        ),
        patch(
            "agent.clients.control_plane.ScenarioClaimSet",
            return_value=non_pending_claim_set,
        ),
    ):
        assert await client.fetch_scenario_claim_set() is None


@pytest.mark.asyncio
async def test_ack_scenario_claim_set_formats_path(client):
    claim_set_id = uuid4()

    with patch.object(client, "request", new=AsyncMock()) as request_mock:
        await client.ack_scenario_claim_set(claim_set_id)

    request_mock.assert_awaited_once_with(
        "POST",
        AGENT_CLAIM_SET_ACK_PATH.format(claim_set_id=str(claim_set_id)),
    )


@pytest.mark.asyncio
async def test_fetch_scenario_run_builds_model(client):
    scenario_run = object()

    with (
        patch.object(
            client, "request", new=AsyncMock(return_value={"id": 1})
        ) as request_mock,
        patch(
            "agent.clients.control_plane.ScenarioRun", return_value=scenario_run
        ) as scenario_run_cls,
    ):
        result = await client.fetch_scenario_run(7, 9)

    assert result is scenario_run
    request_mock.assert_awaited_once()
    scenario_run_cls.assert_called_once_with(**{"id": 1})


@pytest.mark.asyncio
async def test_publish_cluster_snapshot_serializes_payload(client):
    payload = SimpleNamespace(model_dump=lambda **kwargs: {"sync_uuid": "123"})

    with patch.object(client, "request", new=AsyncMock()) as request_mock:
        await client.publish_cluster_snapshot(payload)

    request_mock.assert_awaited_once_with(
        "POST",
        "/api/v1/agent/snapshots/cluster",
        json={"sync_uuid": "123"},
    )
