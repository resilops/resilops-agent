import logging

from agent.clients.control_plane import ControlPlaneClient
from agent.exceptions import ResiliencyPlanExecutionError
from agent.schemas.resiliency import ExperimentDefinition, ResiliencyPlan

logger = logging.getLogger(__name__)


class ResiliencyPlanRunner:
    """
    Executes experiment plan sequentially and emits execution events.

    Responsibilities:
        - Fetch steps from control plane
        - Execute experiment (one-shot)
        - Stop execution on failure if configured
    """

    def __init__(self, client: ControlPlaneClient) -> None:
        self.client = client

    async def run(self, plan: ResiliencyPlan) -> None:
        """
        Raises exception if any of the experiment execution failed
        or some api error
        """
        try:
            for exp_id in plan.experiments:
                _: ExperimentDefinition = await self.client.fetch_experiment(
                    plan_id=plan.id, exp_id=exp_id
                )
        except Exception as e:
            logger.exception("Unhandled error while executing plan %s", plan.id)
            raise ResiliencyPlanExecutionError(
                "ExperimentDefinition plan execution failed",
                context={"plan": plan, "message": str(e)},
            )
