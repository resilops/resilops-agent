import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp

from agent import helper as h
from agent.exceptions import APIRequestError
from agent.models.config import AgentConfigModel

logger = logging.getLogger(__name__)


class BaseAPIClient:
    """
    Base class for asynchronous HTTP clients communicating with the any clients.

    Features:
    - Automatic retries for network errors and 5xx HTTP responses
    - Raises APIRequestError on non-successful responses
    - Supports configurable retry count, delay, and request timeout

    Subclasses must define the `host` property.
    """

    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1  # seconds
    REQUEST_TIMEOUT: float = 3  # seconds

    def __init__(self, config: AgentConfigModel) -> None:
        """
        Initialize the API client with configuration.

        Args:
            config: Agent configuration containing API credentials and host info.
        """
        self.config = config

    @property
    def headers(self) -> Dict[str, str]:
        """
        Return HTTP headers for requests, including authorization.

        Returns:
            Dictionary of headers.
        """
        return {
            "Content-Type": "application/json",
            "RG-X-API-KEY-ID": self.config.api_key_id,
            "RG-X-API-KEY-SECRET": self.config.api_secret_key,
        }

    @property
    def host(self) -> str:
        """
        Base host URL for the API. Must be implemented by subclasses.

        Raises:
            NotImplementedError: if subclass does not define host.
        """
        raise NotImplementedError("Subclasses must define `host` property")

    async def _request(
        self,
        method: str,
        url: str,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a single HTTP request without retries.

        Args:
            method: HTTP method, e.g., 'GET', 'POST'.
            url: Full URL of the request.
            json: Optional JSON body for POST/PUT requests.

        Returns:
            Parsed JSON response.

        Raises:
            APIRequestError: for non-success HTTP responses.
            aiohttp.ClientError: for network errors.
        """
        timeout = aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(
            headers=self.headers, timeout=timeout
        ) as session:
            async with session.request(method, url, json=json) as resp:
                await h.raise_for_status(resp)
                return await resp.json()

    async def request(
        self, method: str, path: str, json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an HTTP request with retry logic.

        Retries are attempted for:
        - Network errors (aiohttp.ClientError)
        - 5xx HTTP responses (via APIRequestError)

        Args:
            method: HTTP method, e.g., 'GET', 'POST'.
            path: API path, appended to the host.
            json: Optional JSON body for POST/PUT requests.

        Returns:
            Parsed JSON response.

        Raises:
            APIRequestError: if all retry attempts fail or a non-retriable status is
            returned.
        """
        url = h.url(self.host, path)
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                return await self._request(method=method, url=url, json=json)
            except (APIRequestError, aiohttp.ClientError) as exc:
                status = getattr(exc, "status", None)
                # Stop retrying if max attempts reached or non-retriable status
                if (
                    attempt >= self.MAX_RETRIES
                    or status in h.non_retriable_status_codes()
                ):
                    logger.error(
                        "Request failed (attempt %d/%d) to %s: %s",
                        attempt,
                        self.MAX_RETRIES,
                        url,
                        exc,
                    )
                    raise

                logger.warning(
                    "Request failed (attempt %d/%d) to %s, retrying in %.1fs: %s",
                    attempt,
                    self.MAX_RETRIES,
                    url,
                    self.RETRY_DELAY,
                    exc,
                )
                await asyncio.sleep(self.RETRY_DELAY)
