import logging
import logging.config
import os
from typing import Any, Dict

import pythonjsonlogger


def setup_logging() -> None:
    """Configure logging using the provided dictionary or the default configuration."""

    log_level = os.getenv("LOG_LEVEL", "INFO")

    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": pythonjsonlogger.json.JsonFormatter,
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
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "chaostoolkit": {
                "handlers": ["console"],
                "level": "WARNING",  # Only warnings or errors from CT
                "propagate": False,
            },
            "agent": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
        },
    }
    config = logging_config
    logging.config.dictConfig(config)
