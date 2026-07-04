from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from agent.clients.base import BaseAPIClient
from agent.exceptions import APIRequestError


class DummyClient(BaseAPIClient):
    @property
    def host(self) -> str:
        return "https://service.example.com"


class NoHostClient(BaseAPIClient):
    pass


class FakeAsyncClient:
    def __init__(self, *, response=None, error=None, **kwargs):
        self.kwargs = kwargs
        self.response = response
        self.error = error
        self.request = AsyncMock(side_effect=self._request)

    async def _request(self, *args, **kwargs):
        if self.error:
            raise self.error
        return self.response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def test_host_property_requires_override(agent_config):
    client = NoHostClient(agent_config)

    with pytest.raises(NotImplementedError):
        _ = client.host


def test_is_retryable_error_uses_status_code():
    assert DummyClient._is_retryable_error(APIRequestError("bad", status_code=500))
    assert not DummyClient._is_retryable_error(APIRequestError("bad", status_code=404))


@pytest.mark.asyncio
async def test__request_merges_headers_and_returns_json(agent_config):
    response = Mock(status_code=200, json=Mock(return_value={"ok": True}))
    response.raise_for_status = Mock()
    created_clients = []

    def build_client(**kwargs):
        fake_client = FakeAsyncClient(response=response, **kwargs)
        created_clients.append(fake_client)
        return fake_client

    with patch("agent.clients.base.httpx.AsyncClient", side_effect=build_client):
        client = DummyClient(agent_config)
        result = await client._request(
            "POST",
            "https://service.example.com/items",
            json={"x": 1},
            headers={"X-Trace": "abc"},
        )

    fake_client = created_clients[0]
    assert result == {"ok": True}
    assert fake_client.kwargs["headers"] == {
        "Content-Type": "application/json",
        "X-Trace": "abc",
    }
    fake_client.request.assert_awaited_once_with(
        "POST",
        "https://service.example.com/items",
        params=None,
        json={"x": 1},
        data=None,
    )


@pytest.mark.asyncio
async def test__request_returns_none_for_204(agent_config):
    response = Mock(status_code=204)
    response.raise_for_status = Mock()
    response.json = Mock()

    with patch(
        "agent.clients.base.httpx.AsyncClient",
        return_value=FakeAsyncClient(response=response),
    ):
        client = DummyClient(agent_config)
        result = await client._request("DELETE", "https://service.example.com/items/1")

    assert result is None
    response.json.assert_not_called()


@pytest.mark.asyncio
async def test__request_wraps_http_status_error(agent_config):
    request = httpx.Request("GET", "https://service.example.com/items")
    response = httpx.Response(503, request=request, text="down")
    error = httpx.HTTPStatusError("boom", request=request, response=response)

    with patch(
        "agent.clients.base.httpx.AsyncClient",
        return_value=FakeAsyncClient(error=error),
    ):
        client = DummyClient(agent_config)
        with pytest.raises(APIRequestError, match="HTTP 503"):
            await client._request("GET", "https://service.example.com/items")


@pytest.mark.asyncio
async def test_request_retries_then_succeeds(agent_config):
    client = DummyClient(agent_config)
    client._request = AsyncMock(
        side_effect=[
            httpx.RequestError(
                "retry",
                request=httpx.Request("GET", "https://service.example.com/items"),
            ),
            {"ok": True},
        ]
    )

    with patch("agent.clients.base.asyncio.sleep", new=AsyncMock()) as sleep_mock:
        result = await client.request("GET", "/items")

    assert result == {"ok": True}
    assert client._request.await_count == 2
    sleep_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_does_not_retry_non_retriable_error(agent_config):
    client = DummyClient(agent_config)
    client._request = AsyncMock(side_effect=APIRequestError("bad", status_code=404))

    with pytest.raises(APIRequestError, match="bad"):
        await client.request("GET", "/items", max_retries=3)

    assert client._request.await_count == 1
