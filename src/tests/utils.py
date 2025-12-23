from typing import Any, Optional
from unittest.mock import AsyncMock, Mock

from yarl import URL


def mock_response(
    *,
    status: int,
    reason: str = "Error",
    url: str = "https://api.example.com/test",
    json_data: Optional[Any] = None,
    text_data: Optional[str] = None,
    json_raises: bool = False,
) -> Mock:
    """Return a mock aiohttp.ClientResponse-like object."""
    return Mock(
        status=status,
        reason=reason,
        url=URL(url),
        json=(
            AsyncMock(side_effect=ValueError("Not JSON"))
            if json_raises
            else AsyncMock(return_value=json_data)
        ),
        text=AsyncMock(return_value=text_data),
    )
