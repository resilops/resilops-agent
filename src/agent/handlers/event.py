import logging

from reslib.schemas.event import ResLibEventPayload

from agent.schemas.event import AgentEventPayload

logger = logging.getLogger(__name__)


class EventHandler:
    """
    Emits agent lifecycle and test execution events as structured logs.

    Each log entry represents a single, immutable event. Logs are JSON-formatted
    and intended to be parsed by Fluent Bit, which forwards them to the control plane.

    Notes:
        - Events are logged at-most-once; the agent does not retry them.
        - This is event-level logging, not debug logging.
        - Do not log full tracebacks or Chaos Toolkit journals here.

    Usage:
        EventHandler.publish(event)

        Args:
            event (AgentEventPayload | ResLibAgentEventPayload): The event to emit.
                - `event_name` represents the type (e.g., EXECUTION_STARTED)
                - `data` contains event-specific metadata (execution_id, activity, etc.)
    """

    @staticmethod
    def publish(event: AgentEventPayload | ResLibEventPayload):
        """Emits agent lifecycle and test execution events as structured logs."""
        logger.info(event.event_name.value, extra=event.model_dump())
