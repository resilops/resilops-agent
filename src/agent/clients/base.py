import asyncio
import logging
from typing import Any, Mapping, Optional

import httpx

from agent import helper as h
from agent.exceptions import APIRequestError
from agent.schemas.config import AgentConfigModel

logger = logging.getLogger(__name__)


class BaseAPIClient:
    """
    Base class for asynchronous HTTP clients.

    This class provides:
        - Asynchronous HTTP requests using `httpx.AsyncClient`.
        - Automatic retries on network errors and 5xx HTTP responses.
        - Raises `APIRequestError` on non-successful responses.
        - Configurable retry count, delay, and request timeout.

    Subclasses must implement the `host` property to define
    the base URL for the API.

    Attributes:
        MAX_RETRIES (int): Maximum number of retry attempts (default: 3)
        RETRY_DELAY (float): Delay between retries in seconds (default: 1)
        REQUEST_TIMEOUT (float): Timeout for a single request in seconds (default: 3)
    """

    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    REQUEST_TIMEOUT: float = 3.0

    def __init__(self, config: AgentConfigModel) -> None:
        """
        Initialize the API client with agent configuration.

        Args:
            config (AgentConfigModel): Agent configuration containing API keys.
        """
        self.config = config

    @property
    def headers(self) -> dict[str, str]:
        """
        Return HTTP headers including authorization keys.

        Returns:
            dict: HTTP headers with 'Content-Type' and API keys.
        """
        return {
            "Content-Type": "application/json",
            "RG-X-API-KEY-ID": self.config.api_key_id,
            "RG-X-API-KEY-SECRET": self.config.api_secret_key,
        }

    @property
    def host(self) -> str:
        """
        Base host URL for the API.

        Raises:
            NotImplementedError: Must be implemented by subclass.
        """
        raise NotImplementedError("Subclasses must define `host` property")

    async def _request(
        self,
        method: str,
        url: str,
        params: Optional[Mapping[str, Any]] = None,
        json: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """
        Execute a single HTTP request without retries.

        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE).
            url (str): Full request URL.
            params (Optional[dict]): Data as request parameters.
            json (Optional[dict]): JSON payload for request body.

        Returns:
            Any: Parsed JSON response.

        Raises:
            APIRequestError: If HTTP response is 4xx/5xx.
            httpx.RequestError: For network-related errors.
        """
        timeout = httpx.Timeout(self.REQUEST_TIMEOUT)
        async with httpx.AsyncClient(headers=self.headers, timeout=timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.request(method, url, params=params)
                else:
                    response = await client.request(method, url, json=json)
                response.raise_for_status()
                return response.json()
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
        params: Optional[Mapping[str, Any]] = None,
        json: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """
        Execute an HTTP request with automatic retries for network
        errors and 5xx HTTP responses.

        Args:
            method (str): HTTP method.
            path (str): API path (appended to host).
            params (Optional[dict]): Data as request parameters.
            json (Optional[dict]): JSON payload for request.

        Returns:
            Any: Parsed JSON response.

        Raises:
            APIRequestError: If max retries exceeded or non-retriable
            error occurs.
        """
        url = h.url(self.host, path)

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                return await self._request(
                    method=method, url=url, params=params, json=json
                )
            except (httpx.RequestError, APIRequestError) as exc:
                # Stop retrying if non-retriable or max attempts reached
                if attempt >= self.MAX_RETRIES:
                    raise

                status_code = getattr(exc, "status_code", None)
                if status_code and status_code in h.non_retriable_status_codes():
                    raise

            logger.warning(
                "Request attempt %d/%d to %s failed, retrying in %.1fs",
                attempt,
                self.MAX_RETRIES,
                url,
                self.RETRY_DELAY,
            )
            await asyncio.sleep(self.RETRY_DELAY)

        return None
