import logging
import uuid
from typing import Any, Optional, Union

from reslib.helpers import BaseTelemetry
from reslib.schemas.telemetry import (
    EventPayload as ReslibEventPayload,
    MetricsPayload as ReslibMetricsPayload,
)

from agent.schemas.event import EventPayload

logger = logging.getLogger(__name__)


class AgentTelemetry:
    """Translate agent and ResLib telemetry payloads into structured logs."""

    @staticmethod
    def _log(
        *,
        name: str,
        payload: Any,
        run_id: Optional[int] = None,
        scenario_id: Optional[int] = None,
    ) -> None:
        """Emit a structured log entry with optional execution context."""
        logger.info(
            name,
            extra={
                **payload.model_dump(mode="json"),
                "ingest_id": str(uuid.uuid4()),  # ingestion id for idempotency
                "run_id": run_id,
                "scenario_id": scenario_id,
            },
        )

    def emit_event(
        self,
        *,
        event: EventPayload | ReslibEventPayload,
        run_id: Optional[int] = None,
        scenario_id: Optional[int] = None,
    ) -> None:
        """Emit an event payload with optional run and scenario identifiers."""
        self._log(
            name=event.event_name.value,  # noqa
            payload=event,
            run_id=run_id,
            scenario_id=scenario_id,
        )

    def emit_metrics(
        self,
        *,
        metrics: ReslibMetricsPayload,
        run_id: int,
        scenario_id: Optional[int] = None,
    ) -> None:
        """Emit a metrics payload with execution context."""
        self._log(
            name=metrics.metrics_name.value,
            payload=metrics,
            run_id=run_id,
            scenario_id=scenario_id,
        )


class RunTelemetry(BaseTelemetry):
    """Execution-scoped telemetry adapter that adds run and scenario context."""

    def __init__(
        self,
        telemetry: AgentTelemetry,
        run_id: int,
        scenario_id: int,
    ):
        """Create a telemetry adapter bound to a specific scenario run."""
        self.telemetry = telemetry
        self.run_id = run_id
        self.scenario_id = scenario_id

    def emit_event(self, *, event: Union[ReslibEventPayload, EventPayload]) -> None:
        """Forward an event with the bound run and scenario IDs."""
        self.telemetry.emit_event(
            event=event,
            run_id=self.run_id,
            scenario_id=self.scenario_id,
        )

    def emit_metrics(self, *, metrics: ReslibMetricsPayload) -> None:
        """Forward metrics with the bound run and scenario IDs."""
        self.telemetry.emit_metrics(
            metrics=metrics,
            run_id=self.run_id,
            scenario_id=self.scenario_id,
        )
