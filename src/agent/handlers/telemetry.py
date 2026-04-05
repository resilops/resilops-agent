import logging
from typing import Any, Optional, Union

from reslib.helpers import BaseTelemetry as LibBaseTelemetry
from reslib.schemas.telemetry import (
    EventPayload as ReslibEventPayload,
    MetricsPayload as ReslibMetricsPayload,
)

from agent.schemas.event import EventPayload

logger = logging.getLogger(__name__)


class AgentTelemetry:
    """
    Central telemetry adapter for emitting ResLib events and metrics
    into the agent's logging/observability pipeline.

    This class acts as a thin translation layer between ResLib's internal
    telemetry models and the agent's runtime context (run, suite, scenario).

    All telemetry is emitted via structured logs using `logger.info(...)`
    with enriched metadata.
    """

    @staticmethod
    def _log(
        *,
        name: str,
        payload: Any,
        run_id: Optional[int] = None,
        suite_id: Optional[int] = None,
        scenario_id: Optional[int] = None,
    ) -> None:
        """
        Emit a structured log entry with execution context.

        Args:
            name:
                Logical name of the event or metric - enum value
                (e.g. `res:event:...` or `res:measurement:...`).
            payload:
                Pydantic model representing the event or metric payload.
            run_id:
                Unique identifier for the current run.
            suite_id:
                Identifier of the test or resilience suite.
            scenario_id:
                Optional identifier for the specific scenario within the suite.
        """
        logger.info(
            name,
            extra={
                **payload.model_dump(mode="json"),
                "run_id": run_id,
                "suite_id": suite_id,
                "scenario_id": scenario_id,
            },
        )

    def emit_event(
        self,
        *,
        event: EventPayload | ReslibEventPayload,
        run_id: Optional[int] = None,
        suite_id: Optional[int] = None,
        scenario_id: Optional[int] = None,
    ) -> None:
        """
        Emit a ResLib or agent-level event with execution context.

        Args:
            event:
                Event payload emitted by ResLib or the agent.
            run_id:
                Unique identifier for the current run.
            suite_id:
                Identifier of the test or resilience suite.
            scenario_id:
                Optional identifier for the scenario.
        """
        self._log(
            name=event.event_name.value,  # noqa
            payload=event,
            run_id=run_id,
            suite_id=suite_id,
            scenario_id=scenario_id,
        )

    def emit_metrics(
        self,
        *,
        metrics: ReslibMetricsPayload,
        run_id: int,
        suite_id: int,
        scenario_id: Optional[int] = None,
    ) -> None:
        """
        Emit a ResLib metrics payload with execution context.

        Args:
            metrics:
                Metrics payload containing measurements and metadata.
            run_id:
                Unique identifier for the current run.
            suite_id:
                Identifier of the test or resilience suite.
            scenario_id:
                Optional identifier for the scenario.
        """
        self._log(
            name=metrics.metrics_name.value,
            payload=metrics,
            run_id=run_id,
            suite_id=suite_id,
            scenario_id=scenario_id,
        )


class ResLibTelemetryWithContext(LibBaseTelemetry):
    """
    Execution-scoped telemetry adapter for ResLib that forwards events
    and metrics to the agent telemetry system with run/suite/scenario context.

    This class allows ResLib code to emit events and metrics as usual,
    but automatically enriches them with the current execution identifiers.
    """

    def __init__(
        self,
        telemetry: AgentTelemetry,
        run_id: int,
        suite_id: int,
        scenario_id: int,
    ):
        """
        Initialize the telemetry adapter with execution context.

        Args:
            telemetry: The agent's telemetry instance to forward events/metrics.
            run_id: Unique identifier for the current run.
            suite_id: Identifier of the current resilience suite.
            scenario_id: Identifier of the specific scenario within the suite.
        """
        self.telemetry = telemetry
        self.run_id = run_id
        self.suite_id = suite_id
        self.scenario_id = scenario_id

    def emit_event(self, *, event: Union[ReslibEventPayload, EventPayload]) -> None:
        """
        Emit an event to the agent telemetry system.

        Both ResLib and agent-native events are supported. The execution
        context (run_id, suite_id, scenario_id) is automatically added.

        Args:
            event: Event payload to be emitted.
        """
        self.telemetry.emit_event(
            event=event,
            run_id=self.run_id,
            suite_id=self.suite_id,
            scenario_id=self.scenario_id,
        )

    def emit_metrics(self, *, metrics: ReslibMetricsPayload) -> None:
        """
        Emit a metrics payload to the agent telemetry system.

        The execution context (run_id, suite_id, scenario_id) is automatically added.

        Args:
            metrics: Metrics payload to be emitted.
        """
        self.telemetry.emit_metrics(
            metrics=metrics,
            run_id=self.run_id,
            suite_id=self.suite_id,
            scenario_id=self.scenario_id,
        )
