import pytest

from agent import helper as h
from agent.exceptions import APIRequestError
from tests.utils import mock_response


def test_url_joins_host_and_path():
    """Join host and absolute path into a valid URL."""
    assert (
        h.url("https://api.example.com", "/v1/users")
        == "https://api.example.com/v1/users"
    )


def test_url_handles_missing_slash():
    """Correctly handle paths without a leading slash."""
    assert (
        h.url("https://api.example.com/", "v1/users")
        == "https://api.example.com/v1/users"
    )


def test_url_overwrites_path():
    """Ensure absolute paths replace any existing host path."""
    assert (
        h.url("https://api.example.com/v1/", "/health")
        == "https://api.example.com/health"
    )


@pytest.mark.asyncio
async def test_raise_for_status_no_error_on_2xx():
    """Do not raise an exception for successful (2xx) responses."""
    resp = mock_response(status=200)

    # Should not raise
    await h.raise_for_status(resp)


@pytest.mark.asyncio
async def test_raise_for_status_with_json_body():
    """Raise APIRequestError and attach parsed JSON error details."""
    resp = mock_response(
        status=400,
        reason="Bad Request",
        json_data={"error": "invalid input"},
    )

    with pytest.raises(APIRequestError) as exc:
        await h.raise_for_status(resp)

    err = exc.value
    assert err.status == 400
    assert err.context["reason"] == "Bad Request"
    assert err.context["data"] == {"error": "invalid input"}


@pytest.mark.asyncio
async def test_raise_for_status_with_text_body():
    """Fallback to raw text when the response body is not valid JSON."""
    resp = mock_response(
        status=500,
        reason="Internal Server Error",
        text_data="server exploded",
        json_raises=True,
    )

    with pytest.raises(APIRequestError) as exc:
        await h.raise_for_status(resp)

    err = exc.value
    assert err.status == 500
    assert err.context["reason"] == "Internal Server Error"
    assert err.context["body"] == "server exploded"


@pytest.mark.asyncio
async def test_raise_for_status_includes_url():
    """Include request URL in the exception context."""
    resp = mock_response(
        status=404,
        url="https://api.example.com/missing",
        json_data={"detail": "not found"},
    )

    with pytest.raises(APIRequestError) as exc:
        await h.raise_for_status(resp)

    err = exc.value
    assert err.context["url"] == "https://api.example.com/missing"


def test_non_retriable_status_codes():
    """Return the expected set of HTTP status codes that should not be retried."""
    expected = {400, 401, 403, 404, 409, 422}
    assert set(h.non_retriable_status_codes()) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("status", h.non_retriable_status_codes())
async def test_raise_for_status_non_retriable(status):
    """Ensure non-retriable HTTP errors always raise APIRequestError."""
    resp = mock_response(
        status=status,
        reason="Error",
        json_data={"detail": "fail"},
    )

    with pytest.raises(APIRequestError):
        await h.raise_for_status(resp)
