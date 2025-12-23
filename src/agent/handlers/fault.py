import logging

from chaoslib.experiment import run_experiment

from agent.clients.control_plane import ControlPlaneClient
from agent.exceptions import FaultPlanExecutionFailedException
from agent.models.fault import FaultModel, FaultPlanModel

logger = logging.getLogger(__name__)


class FaultPlanExecutionHandler:
    """
    Executes a fault plan sequentially and emits execution events.

    Responsibilities:
        - Fetch faults from control plane
        - Execute chaos experiments (one-shot)
        - Stop execution on failure if configured
    """

    def __init__(
        self,
        client: ControlPlaneClient,
    ) -> None:
        self.client = client

    async def run_plan(self, plan: FaultPlanModel) -> None:
        """Raises exception if any of the fault execution failed or some api error"""
        failures: list[dict[str, str]] = []
        for fault_id in plan.faults:
            try:
                fault: FaultModel = await self.client.fetch_fault(fault_id)

                result = run_experiment(fault.dict())
                failed = [
                    {
                        "fault_id": fault_id,
                        "message": item.get("exception", ["Unknown error"])[-1],
                    }
                    for item in result.get("run", [])
                    if item.get("status") == "failed"
                ]
                failures.extend(failed)

                if failed and plan.execution.stop_on_failure:
                    break
            except Exception as e:
                logger.exception(
                    "Unhandled error while executing fault plan %s", plan.id
                )
                failures.append({"fault_id": fault_id, "message": str(e)})
                break

        if failures:
            raise FaultPlanExecutionFailedException(
                "Fault plan execution failed",
                context={"plan": plan, "failures": failures},
            )
