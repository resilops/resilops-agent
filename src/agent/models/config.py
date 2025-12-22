from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfigModel(BaseSettings):
    """
    Configuration for the Fault agent.
    Environment variables are prefixed with `RESILTY_FAULT_AGENT_`.
    """

    model_config = SettingsConfigDict(env_prefix="RESILTY_FAULT_AGENT_")

    # API Credentials
    api_key_id: str = Field(
        ..., description="API Key ID for authenticating with the control plane API"
    )
    api_secret_key: str = Field(
        ..., description="Secret API Key for authenticating with the control plane API"
    )

    # Control plane hosts
    control_plane_api_host: str = Field(
        "http://controlplane:8000",
        description="Base URL for the Fault control plane API",
    )

    # Task intervals (in seconds)
    heartbeat_interval: int = Field(
        3, description="Interval between heartbeat signals to the control plane"
    )
    runner_interval: int = Field(
        2, description="Interval for executing queued fault plans"
    )
    fault_plan_poll_interval: int = Field(
        2, description="Interval for polling the control plane for new fault plans"
    )
    event_publish_interval: int = Field(
        5, description="Interval for publishing the event"
    )
