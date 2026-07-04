from types import SimpleNamespace
from uuid import uuid4

import pytest

from agent.schemas.config import AgentConfig
from agent.schemas.scenario import ScenarioClaim, ScenarioClaimSet


@pytest.fixture
def agent_config() -> AgentConfig:
    return AgentConfig(
        auth_service_host="https://auth.example.com",
        auth_service_client_id="client-id",
        auth_service_client_secret="client-secret",
        control_plane_api_host="https://cp.example.com",
        namespace="resilops",
        target_namespaces="team-a, team-b",
        config_version="cfg-1",
    )


@pytest.fixture
def sample_claim() -> ScenarioClaim:
    return ScenarioClaim(
        id=uuid4(),
        run_id=101,
        scenario_id=7,
        position=1,
    )


@pytest.fixture
def sample_claim_set(sample_claim: ScenarioClaim) -> ScenarioClaimSet:
    return ScenarioClaimSet(
        id=uuid4(),
        workload_id=55,
        quality_gate_run_id=None,
        status="pending",
        claims=[sample_claim],
    )


@pytest.fixture
def sample_token_response() -> dict:
    return {
        "access_token": "token-123",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "scope-a",
    }


@pytest.fixture
def sample_run_config() -> SimpleNamespace:
    return SimpleNamespace(kind="scenario")
