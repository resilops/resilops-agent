from datetime import datetime, timedelta, timezone

from agent.schemas.event import EventEnum, EventPayload
from agent.schemas.heartbeat import HeartbeatRequest, HeartbeatResponse
from agent.schemas.state import AgentHealthState, AgentState, RunnerState, RunnerStatus
from agent.schemas.token import AccessToken


def test_access_token_expires_at_and_is_expired():
    created_at = datetime.now(timezone.utc) - timedelta(seconds=20)
    token = AccessToken(
        access_token="abc",
        expires_in=10,
        token_type="Bearer",
        created_at=created_at,
    )

    assert token.expires_at == created_at + timedelta(seconds=5)
    assert token.is_expired is True


def test_event_and_heartbeat_models_use_expected_defaults():
    event = EventPayload(event_name=EventEnum.SCENARIO_QUEUED)
    request = HeartbeatRequest(version="1.0.0", config_version="cfg-1")
    response = HeartbeatResponse(health="healthy")

    assert event.type == "event"
    assert event.source == "agent"
    assert request.reason is None
    assert response.health.value == "healthy"


def test_state_models_have_expected_defaults():
    runner_state = RunnerState()
    agent_state = AgentState()

    assert runner_state.state == RunnerStatus.IDLE
    assert runner_state.claim_set is None
    assert agent_state.health == AgentHealthState.UNKNOWN
    assert agent_state.running_workers == []
