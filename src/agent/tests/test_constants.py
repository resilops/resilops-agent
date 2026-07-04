from agent.constants import (
    AgentHealthEnum,
    AgentOAuthScopes,
    ScenarioClaimSetExecutionMode,
    ScenarioClaimStatus,
)


def test_agent_oauth_scopes_renders_space_delimited_string():
    scopes = AgentOAuthScopes.scopes()

    assert AgentOAuthScopes.event_create.value in scopes
    assert AgentOAuthScopes.claim_ack.value in scopes
    assert scopes.count(" ") == len(AgentOAuthScopes) - 1


def test_enums_expose_expected_values():
    assert AgentHealthEnum.healthy.value == "healthy"
    assert ScenarioClaimStatus.acknowledged.value == "acknowledged"
    assert (
        ScenarioClaimSetExecutionMode.continue_on_failure.value == "continue_on_failure"
    )
