from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel


class ResiliencyScenarioStatusEnum(Enum):

    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"


class ResiliencyScenario(BaseModel):

    id: int
    run_id: int
    name: str
    title: str
    description: str
    template: Dict[str, Any]
    steps: List[Dict[str, Any]]
    observer: Dict[str, Any]
    state: ResiliencyScenarioStatusEnum = ResiliencyScenarioStatusEnum.PENDING


M2M_TOKEN_RESPONSE = {
    "access_token": "dummy_access_token_abc123xyz",
    "expires_in": 157680000,
    "scope": "read write",
    "token_type": "Bearer",
    "created_at": datetime.now(timezone.utc).isoformat(),
}
