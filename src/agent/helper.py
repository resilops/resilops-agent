import urllib.parse
from typing import Any, Dict, Iterable

import aiohttp

from agent.exceptions import APIRequestError


def url(host: str, path: str) -> str:
    """Safely join host and path into a full URL."""
    return urllib.parse.urljoin(host, path)


async def raise_for_status(resp: aiohttp.ClientResponse) -> None:
    """
    Raise APIRequestError for non-2xx HTTP responses. Reads response body once and
    attaches structured context.
    """
    if resp.status < 400:
        return

    context: Dict[str, Any] = {
        "reason": resp.reason,
        "url": str(resp.url),
    }
    try:
        context["data"] = await resp.json()
    except Exception:
        context["body"] = await resp.text()

    raise APIRequestError(
        message=f"HTTP {resp.status} {resp.reason}", status=resp.status, context=context
    )


def non_retriable_status_codes() -> Iterable[int]:
    """Do not retry on following status codes"""
    return {
        400,  # Bad request
        401,  # Unauthorized
        403,  # Forbidden
        404,  # Not found
        409,  # Conflict
        422,  # Validation error
    }
