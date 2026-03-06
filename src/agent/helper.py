import os
import urllib.parse
from typing import Dict, Iterable

from agent.schemas.suite import ResiliencySuite


def url(host: str, path: str) -> str:
    """Safely join host and path into a full URL."""
    return urllib.parse.urljoin(host, path)


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


def get_ids_from_suite(suite: ResiliencySuite) -> Dict:
    return {"suite_id": suite.id, "run_id": suite.run_id}


def get_agent_id() -> str:
    """Get agent name"""
    agent_name: str = os.getenv("POD_NAME")
    if not agent_name:
        raise EnvironmentError("Environment variable POD_NAME not set")
    return agent_name
