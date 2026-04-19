import logging
import logging.config
import os
from datetime import datetime, timezone
from typing import Any, Dict

import pythonjsonlogger


class UTCJsonFormatter(pythonjsonlogger.json.JsonFormatter):
    """JSON formatter that emits RFC 3339 timestamps in UTC."""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        """Serialize log time as ISO 8601 / RFC 3339 UTC."""
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def setup_logging() -> None:
    """Configure logging using the provided dictionary or the default configuration."""

    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_path = os.getenv("LOG_FILE", "/var/log/agent/agent.log")
    max_mb = int(os.getenv("LOG_MAX_MB", 50))
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", 3))

    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": UTCJsonFormatter,
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                "rename_fields": {"asctime": "time", "levelname": "level"},
                "json_indent": None,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "level": "DEBUG",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": log_path,
                "formatter": "json",
                "level": "DEBUG",
                "maxBytes": max_mb * 1024 * 1024,
                "backupCount": backup_count,
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "agent": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "httpx": {
                "handlers": ["console", "file"],
                "level": "WARNING",  # silence INFO request logs
                "propagate": False,
            },
        },
    }
    config = logging_config
    logging.config.dictConfig(config)
