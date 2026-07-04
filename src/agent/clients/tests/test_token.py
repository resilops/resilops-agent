from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from agent.clients.token import AuthServiceClient
from agent.exceptions import AuthServiceError
from agent.schemas.token import AccessToken


@pytest.mark.asyncio
async def test_get_m2m_token_returns_cached_token(agent_config):
    client = AuthServiceClient(agent_config)
    client._auth_m2m_token = AccessToken(
        access_token="cached",
        expires_in=3600,
        token_type="Bearer",
        created_at=datetime.now(timezone.utc) - timedelta(seconds=60),
    )

    with patch.object(client, "request", new=AsyncMock()) as request_mock:
        token = await client.get_m2m_token()

    assert token.access_token == "cached"
    request_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_m2m_token_fetches_and_caches_token(
    agent_config, sample_token_response
):
    client = AuthServiceClient(agent_config)

    with patch.object(
        client, "request", new=AsyncMock(return_value=sample_token_response)
    ) as request_mock:
        token = await client.get_m2m_token()

    assert token.access_token == sample_token_response["access_token"]
    assert client._auth_m2m_token == token
    assert request_mock.await_count == 1


@pytest.mark.asyncio
async def test_get_m2m_token_wraps_failures(agent_config):
    client = AuthServiceClient(agent_config)

    with patch.object(
        client, "request", new=AsyncMock(side_effect=RuntimeError("boom"))
    ):
        with pytest.raises(AuthServiceError, match="M2M access token request failed"):
            await client.get_m2m_token()
