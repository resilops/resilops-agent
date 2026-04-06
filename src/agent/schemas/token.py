from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel, Field


class M2MAccessTokenResponse(BaseModel):
    """Access token response for M2M"""

    access_token: str = Field(..., description="Short lived access token")
    expires_in: int = Field(..., description="Expiration in seconds")
    token_type: str = Field(..., description="Token type")
    scope: Optional[str] = Field(default=None, description="Requested scopes")

    # internal field (not from API)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def expires_at(self) -> datetime:
        return self.created_at + timedelta(seconds=self.expires_in - 5)

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at
