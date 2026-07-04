from unittest.mock import patch

import pytest

from agent import helper


def test_join_url_handles_absolute_and_relative_paths():
    assert helper.join_url("https://api.example.com", "/v1/items") == (
        "https://api.example.com/v1/items"
    )
    assert helper.join_url("https://api.example.com/", "v1/items") == (
        "https://api.example.com/v1/items"
    )


def test_get_agent_id_returns_pod_name():
    with patch.dict("os.environ", {"POD_NAME": "agent-pod-1"}, clear=False):
        assert helper.get_agent_id() == "agent-pod-1"


def test_get_agent_id_raises_when_missing():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(EnvironmentError, match="POD_NAME"):
            helper.get_agent_id()
