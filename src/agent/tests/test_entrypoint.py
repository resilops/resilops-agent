from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from agent import entrypoint


@pytest.mark.asyncio
async def test_main_builds_runtime_and_runs_lifecycle(agent_config):
    control_plane_client = object()
    state_handler = object()
    telemetry = object()
    leader_election = object()
    lifecycle_manager = SimpleNamespace(run=AsyncMock())

    with (
        patch("agent.entrypoint.setup_logging") as setup_logging_mock,
        patch("agent.entrypoint.AgentConfig", return_value=agent_config),
        patch("agent.entrypoint.AuthServiceClient", return_value=object()),
        patch("agent.entrypoint.ControlPlaneClient", return_value=control_plane_client),
        patch("agent.entrypoint.AgentStateHandler", return_value=state_handler),
        patch("agent.entrypoint.AgentTelemetry", return_value=telemetry),
        patch(
            "agent.entrypoint.KubernetesLeaderElection",
            return_value=leader_election,
        ),
        patch("agent.entrypoint.HeartbeatWorker", return_value="hb"),
        patch("agent.entrypoint.ScenarioSchedulerWorker", return_value="sched"),
        patch("agent.entrypoint.ScenarioRunner", return_value="runner"),
        patch("agent.entrypoint.ScenarioRunnerWorker", return_value="run-worker"),
        patch("agent.entrypoint.SnapshotHandler", return_value="snapshot-handler"),
        patch("agent.entrypoint.SnapshotWorker", return_value="snapshot-worker"),
        patch("agent.entrypoint.WorkerManager", return_value="manager"),
        patch(
            "agent.entrypoint.LifecycleManager",
            return_value=lifecycle_manager,
        ),
    ):
        await entrypoint.main()

    setup_logging_mock.assert_called_once()
    lifecycle_manager.run.assert_awaited_once()


def test_run_invokes_asyncio_main():
    def close_coro(coro):
        coro.close()

    with patch("agent.entrypoint.asyncio.run", side_effect=close_coro) as run_mock:
        entrypoint.run()

    run_mock.assert_called_once()
