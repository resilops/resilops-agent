import pytest

from agent.handlers.state import AgentStateHandler


def test_runner_state_lifecycle(sample_claim_set):
    handler = AgentStateHandler()

    assert handler.runner.is_idle
    handler.runner.enqueue(sample_claim_set)
    assert handler.runner.is_queued
    assert handler.runner.current_claim_set == sample_claim_set

    handler.runner.mark_running()
    handler.runner.reset_to_idle()
    assert handler.runner.is_idle
    assert handler.runner.current_claim_set is None


def test_runner_state_rejects_invalid_transitions(sample_claim_set):
    handler = AgentStateHandler()

    with pytest.raises(RuntimeError, match="no claim set queued"):
        handler.runner.mark_running()

    handler.runner.enqueue(sample_claim_set)
    with pytest.raises(RuntimeError, match="slot is busy"):
        handler.runner.enqueue(sample_claim_set)


def test_agent_state_tracks_health_and_workers():
    handler = AgentStateHandler()
    worker_tasks = [object(), object()]

    handler.agent.register_workers(worker_tasks)
    handler.agent.set_health(True)
    assert handler.agent.current_workers == worker_tasks
    assert handler.agent.is_healthy

    handler.agent.set_health(False)
    assert not handler.agent.is_healthy
