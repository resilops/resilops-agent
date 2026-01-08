import logging

from chaoslib.experiment import run_experiment

from agent.clients.control_plane import ControlPlaneClient
from agent.exceptions import ResiliencyPlanExecutionError
from agent.schemas.resiliency import ExperimentStepModel, ResiliencyPlanModel

logger = logging.getLogger(__name__)


class ResiliencyPlanExecutionHandler:
    """
    Executes a resiliency plan sequentially and emits execution events.

    Responsibilities:
        - Fetch steps from control plane
        - Execute step (experiment) (one-shot)
        - Stop execution on failure if configured
    """

    def __init__(self, client: ControlPlaneClient) -> None:
        self.client = client

    async def run_plan(self, plan: ResiliencyPlanModel) -> None:
        """Raises exception if any of the step execution failed or some api error"""
        failures: list[dict[str, str]] = []
        for step_id in plan.steps:
            try:
                step: ExperimentStepModel = await self.client.fetch_plan_step(
                    plan_id=plan.id, step_id=step_id
                )

                result = run_experiment(step.dict())
                failed = [
                    {
                        "step_id": step_id,
                        "message": item.get("exception", ["Unknown error"])[-1],
                    }
                    for item in result.get("run", [])
                    if item.get("status") == "failed"
                ]
                failures.extend(failed)

                if failed and plan.execution.stop_on_failure:
                    break
            except Exception as e:
                # In case of API fault even after retry, we do not want to proceed
                # further, which can be potentially harmful.
                logger.exception(
                    "Unhandled error while executing resiliency plan %s", plan.id
                )
                failures.append({"step_id": step_id, "message": str(e)})
                break

        if failures:
            raise ResiliencyPlanExecutionError(
                "Resiliency plan execution failed",
                context={"plan": plan, "failures": failures},
            )
