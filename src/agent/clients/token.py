import asyncio
import logging
from typing import Optional

import httpx

from agent.clients.base import BaseAPIClient
from agent.constants import (
    AUTH_SERVICE_M2M_TOKEN_ISSUE_PATH,
    CLIENT_CREDENTIALS_GRANT_TYPE,
    AgentOAuthScopes,
)
from agent.exceptions import AuthServiceError
from agent.schemas.config import AgentConfigModel
from agent.schemas.token import M2MAccessTokenResponse

logger = logging.getLogger(__name__)


class AuthServiceClient(BaseAPIClient):
    """Client for authentication-related upstream API operations."""

    def __init__(self, config: AgentConfigModel):
        super().__init__(config=config)
        self._token_lock = asyncio.Lock()
        self._auth_m2m_token: Optional[M2MAccessTokenResponse] = None

    @property
    def host(self) -> str:
        """Return the host endpoint URL."""
        return self.config.auth_service_host

    async def get_m2m_token(self) -> M2MAccessTokenResponse:
        """
        Retrieve a machine-to-machine (M2M) access token using client credentials.

        This method implements in-memory caching and concurrency control to avoid
        unnecessary token requests:

        - Returns the cached token if it exists and is not expired.
        - Uses an asyncio lock to ensure only one coroutine refreshes the token
          at a time when expired.
        - Performs a double-check inside the lock to prevent duplicate refreshes
          under concurrent access.
        - Requests a new token from the auth service using HTTP Basic authentication
          (client_id + client_secret) when needed.

        Returns:
            M2MAccessTokenResponse: A valid access token response containing the
            token, expiration, and scope.

        Raises:
            APIRequestError: If the upstream auth service request fails.
        """
        if self._auth_m2m_token and not self._auth_m2m_token.is_expired:
            return self._auth_m2m_token

        async with self._token_lock:
            if self._auth_m2m_token and not self._auth_m2m_token.is_expired:
                return self._auth_m2m_token
            try:
                resp = await self.request(
                    "POST",
                    AUTH_SERVICE_M2M_TOKEN_ISSUE_PATH,
                    auth=httpx.BasicAuth(
                        self.config.auth_service_client_id.get_secret_value(),
                        self.config.auth_service_client_secret.get_secret_value(),
                    ),
                    data={
                        "scope": AgentOAuthScopes.scopes(),
                        "grant_type": CLIENT_CREDENTIALS_GRANT_TYPE,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    max_retries=0,  # No retries for post
                )
            except Exception:
                logger.exception("M2M access token request failed")
                raise AuthServiceError("M2M access token request failed")

            response = M2MAccessTokenResponse(**resp)
            self._auth_m2m_token = response

        return response
