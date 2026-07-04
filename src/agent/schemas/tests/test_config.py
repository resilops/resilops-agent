from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

import pytest

from agent.exceptions import ConfigError
from agent.schemas import config as config_module
from agent.schemas.config import AgentConfig


def test_agent_config_parses_target_namespaces_and_exposes_app_version(agent_config):
    assert agent_config.target_namespaces == ["team-a", "team-b"]
    assert isinstance(agent_config.app_version, str)


def test_parse_target_namespaces_rejects_invalid_values():
    with pytest.raises(ConfigError, match="comma-separated string"):
        AgentConfig.parse_target_namespaces(["bad"])

    with pytest.raises(ConfigError, match="at least one namespace"):
        AgentConfig.parse_target_namespaces(" , ")


def test_get_app_version_raises_when_package_metadata_missing():
    with patch("agent.schemas.config.version", side_effect=PackageNotFoundError):
        with pytest.raises(
            ConfigError, match="Application build does not have app version"
        ):
            config_module._get_app_version()
