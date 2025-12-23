import logging
from typing import Any, Dict

from agent.models.event import AgentEventEnum

logger = logging.getLogger(__name__)


class EventHandler:
    """
    Emits agent lifecycle and chaos execution events as structured logs.

    Notes:
        - Events are logged using the configured JSON logger.
        - Each log entry represents a single immutable event.
        - Fluent Bit is responsible for parsing these logs as JSON
          and forwarding them to the control plane.
        - Events are at-most-once and are not retried by the agent.

    Usage:
        - `event_name` represents the event type (e.g. EXECUTION_STARTED).
        - `data` contains event-specific metadata (execution_id, activity, etc).

    Important:
        - This is event-level logging, not debug logging.
        - Do not log full tracebacks or Chaos Toolkit journals here.
    """

    def push(self, name: AgentEventEnum, data: Dict[Any, Any]):
        logger.info(name.value, extra={**data, "event_name": name.value})
