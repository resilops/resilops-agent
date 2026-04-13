import os
import urllib.parse
from typing import Final

NON_RETRIABLE_STATUS_CODES: Final[frozenset[int]] = frozenset(
    {
        400,  # Bad request
        401,  # Unauthorized
        403,  # Forbidden
        404,  # Not found
        409,  # Conflict
        422,  # Validation error
    }
)


def join_url(host: str, path: str) -> str:
    """Safely join host and path into a full URL."""
    return urllib.parse.urljoin(host, path)


def get_agent_id() -> str:
    """Return the agent identifier from the pod name environment variable."""
    agent_name: str = os.getenv("POD_NAME")
    if not agent_name:
        raise EnvironmentError("Environment variable POD_NAME not set")
    return agent_name
