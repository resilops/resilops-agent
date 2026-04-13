import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from agent import helper as h
from agent.exceptions import APIRequestError
from agent.schemas.config import AgentConfigModel

logger = logging.getLogger(__name__)


class BaseAPIClient:
    """Base asynchronous HTTP client with retry handling."""

    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    REQUEST_TIMEOUT: float = 3.0

    def __init__(self, config: AgentConfigModel) -> None:
        """Store shared configuration for API clients."""
        self.config = config

    async def get_headers(self) -> Dict[str, str]:  # noqa
        """Return default request headers."""
        return {"Content-Type": "application/json"}

    @property
    def host(self) -> str:
        """Return the base host URL for the API."""
        raise NotImplementedError("Subclasses must define `host` property")

    @staticmethod
    def _is_retryable_error(error: Exception) -> bool:
        """Return whether a request error should be retried."""
        status_code = getattr(error, "status_code", None)
        return status_code not in h.NON_RETRIABLE_STATUS_CODES

    async def _request(
        self,
        method: str,
        url: str,
        auth: Optional[httpx.Auth] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Execute a single HTTP request without retry handling."""
        timeout = httpx.Timeout(self.REQUEST_TIMEOUT)

        default_headers = await self.get_headers()
        headers = headers or {}

        # Mutation safe for retries
        headers = {**default_headers, **headers}

        async with httpx.AsyncClient(
            headers=headers, auth=auth, timeout=timeout
        ) as client:
            try:
                response = await client.request(
                    method, url, params=params, json=json, data=data
                )
                response.raise_for_status()
                return None if response.status_code == 204 else response.json()
            except httpx.HTTPStatusError as exc:
                raise APIRequestError(
                    f"HTTP {exc.response.status_code} error for {url}",
                    status_code=exc.response.status_code,
                    context={"response": exc.response.text},
                ) from exc

    async def request(
        self,
        method: str,
        path: str,
        auth: Optional[httpx.Auth] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Execute an HTTP request with retry handling for transient failures."""
        retry_limit = self.MAX_RETRIES if max_retries is None else max(1, max_retries)
        url = h.join_url(self.host, path)

        for attempt in range(1, retry_limit + 1):
            try:
                return await self._request(
                    method=method,
                    url=url,
                    auth=auth,
                    params=params,
                    json=json,
                    data=data,
                    headers=headers,
                )
            except (httpx.RequestError, APIRequestError) as exc:
                if attempt >= retry_limit or not self._is_retryable_error(exc):
                    raise

            logger.warning(
                "Request attempt %d/%d to %s failed, retrying in %.1fs",
                attempt,
                retry_limit,
                url,
                self.RETRY_DELAY,
            )
            await asyncio.sleep(self.RETRY_DELAY)

        return None
