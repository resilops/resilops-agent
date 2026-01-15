import logging

from agent.clients.control_plane import ControlPlaneClient
from agent.exceptions import ResiliencySuiteExecutionError
from agent.schemas.suite import ResiliencyScenario, ResiliencySuite

logger = logging.getLogger(__name__)


class ResiliencySuiteRunner:
    """
    Executes scenarios sequentially and emits execution events.

    Responsibilities:
        - Fetch scenarios from control plane
        - Execute suite (one-shot)
        - Stop execution on failure if configured
    """

    def __init__(self, client: ControlPlaneClient) -> None:
        self.client = client

    async def run(self, suite: ResiliencySuite) -> None:
        """
        Raises exception if any of the scenario execution failed
        or some api error
        """
        try:
            for scenario_id in suite.scenarios:
                _: ResiliencyScenario = await self.client.fetch_scenario(
                    suite_id=suite.id, scenario_id=scenario_id
                )
        except Exception as e:
            logger.exception("Unhandled error while executing suite %s", suite.id)
            raise ResiliencySuiteExecutionError(
                "Suite execution failed",
                context={"suite": suite, "message": str(e)},
            )
