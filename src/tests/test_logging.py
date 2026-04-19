import logging
import os
import re

import pythonjsonlogger

from agent.logging import UTCJsonFormatter, setup_logging


def test_setup_logging_creates_loggers(monkeypatch):
    """Test that loggers are configured with the correct levels and handlers."""
    # Force LOG_LEVEL environment variable
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    setup_logging()

    # Root logger
    root_logger = logging.getLogger()
    assert any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers)
    assert root_logger.level == logging.DEBUG

    # agent logger
    agent_logger = logging.getLogger("agent")
    assert any(isinstance(h, logging.StreamHandler) for h in agent_logger.handlers)
    assert agent_logger.level == logging.DEBUG

    # chaostoolkit logger
    ct_logger = logging.getLogger("chaostoolkit")
    assert any(isinstance(h, logging.StreamHandler) for h in ct_logger.handlers)
    assert ct_logger.level == logging.WARNING


def test_default_log_level(monkeypatch):
    """Test that default LOG_LEVEL is INFO if not set."""
    # Remove LOG_LEVEL if present
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    setup_logging()

    root_logger = logging.getLogger()
    agent_logger = logging.getLogger("agent")

    assert root_logger.level == logging.INFO
    assert agent_logger.level == logging.INFO


def test_logging_output_format_handler_type():
    """Ensure the logger uses JsonFormatter."""
    os.environ["LOG_LEVEL"] = "DEBUG"
    setup_logging()
    logger = logging.getLogger("agent")
    handler = logger.handlers[0]
    assert isinstance(handler.formatter, pythonjsonlogger.json.JsonFormatter)


def test_logging_integration_handler_types_and_levels():
    """
    Ensure agent and chaostoolkit loggers have correct
    handlers, formatters, and levels.
    """
    os.environ["LOG_LEVEL"] = "DEBUG"
    setup_logging()

    # Agent logger
    agent_logger = logging.getLogger("agent")
    assert len(agent_logger.handlers) > 0
    assert isinstance(
        agent_logger.handlers[0].formatter, pythonjsonlogger.json.JsonFormatter
    )
    assert agent_logger.level == logging.DEBUG

    # chaostoolkit logger
    ct_logger = logging.getLogger("chaostoolkit")
    assert len(ct_logger.handlers) > 0
    assert isinstance(
        ct_logger.handlers[0].formatter, pythonjsonlogger.json.JsonFormatter
    )
    assert ct_logger.level == logging.WARNING

    # Root logger
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) > 0
    assert isinstance(
        root_logger.handlers[0].formatter, pythonjsonlogger.json.JsonFormatter
    )
    assert root_logger.level == logging.DEBUG


def test_utc_json_formatter_emits_rfc3339_utc_timestamp():
    """Ensure timestamps are emitted as RFC 3339 UTC strings."""
    formatter = UTCJsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "time", "levelname": "level"},
        json_indent=None,
    )
    record = logging.LogRecord(
        name="agent",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.created = 1_700_000_000.123

    output = formatter.format(record)

    assert '"time": "2023-11-14T22:13:20.123Z"' in output
    assert re.search(r'"time": "\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z"', output)
