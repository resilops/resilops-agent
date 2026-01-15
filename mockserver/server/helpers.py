import asyncio
import random
from typing import Dict, List, Optional

from fastapi import status
from fastapi.responses import JSONResponse
from server import constants


async def maybe_fail(
    failure_codes: Optional[List[int]] = None,
) -> Optional[JSONResponse]:
    """
    Randomly fail requests based on ERROR_RATE.

    Args:
        failure_codes: List of HTTP status codes to randomly choose from if failing.

    Returns:
        JSONResponse with error if failing, else None.
    """
    failure_codes = failure_codes or [status.HTTP_500_INTERNAL_SERVER_ERROR]
    if random.random() < constants.ERROR_RATE:
        return JSONResponse(
            {"error": "Simulated server error"},
            status_code=random.choice(failure_codes),
        )
    return None


async def maybe_delay() -> None:
    """Introduce a random delay to simulate network latency."""
    await asyncio.sleep(random.uniform(0, constants.MAX_DELAY))


def get_resiliency_suite() -> Dict:
    """Returns a respective resiliency suite"""
    return (
        constants.RESILIENCY_SUITE
        if random.random() > constants.RESILIENCY_SUITE_EMPTY_RATE
        else constants.RESILIENCY_EMPTY_SUITE
    )


def get_scenario() -> Dict:
    """Returns a respective resiliency scenario"""
    return constants.RESILIENCY_SCENARIO
