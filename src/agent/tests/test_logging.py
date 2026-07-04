import logging
import re
from unittest.mock import patch

import pythonjsonlogger

from agent.logging import UTCJsonFormatter, setup_logging


def test_setup_logging_uses_env_configuration():
    with patch("logging.config.dictConfig") as dict_config:
        with patch.dict(
            "os.environ",
            {
                "LOG_LEVEL": "DEBUG",
                "LOG_FILE": "/tmp/agent.log",
                "LOG_MAX_MB": "7",
                "LOG_BACKUP_COUNT": "9",
            },
            clear=False,
        ):
            setup_logging()

    config = dict_config.call_args.args[0]
    assert config["loggers"]["agent"]["level"] == "DEBUG"
    assert config["handlers"]["file"]["filename"] == "/tmp/agent.log"
    assert config["handlers"]["file"]["maxBytes"] == 7 * 1024 * 1024
    assert config["handlers"]["file"]["backupCount"] == 9


def test_utc_json_formatter_emits_rfc3339_utc_timestamp():
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

    assert isinstance(formatter, pythonjsonlogger.json.JsonFormatter)
    assert re.search(r'"time": "\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z"', output)
