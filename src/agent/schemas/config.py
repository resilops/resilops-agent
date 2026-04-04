from importlib.metadata import PackageNotFoundError, version
from typing import Annotated, List

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from agent.exceptions import ConfigError


def _get_app_version() -> str:
    """Version of the installed resilience-agent package."""
    try:
        app_version = version("resilience-agent")
    except PackageNotFoundError as exc:
        raise ConfigError("Application build does not have app version") from exc

    if not app_version:
        raise ConfigError("Application build does not have app version")

    return app_version


_APP_VERSION = _get_app_version()


class AgentConfigModel(BaseSettings):
    """
    Configuration for the resiliency-agent.
    Environment variables are prefixed with `RESILTY_AGENT_`.
    """

    model_config = SettingsConfigDict(env_prefix="RESILTY_AGENT_")

    # Resilty Token service
    auth_service_host: str = Field(..., description="Base URL for the auth service API")
    auth_service_client_id: SecretStr = Field(
        ..., description="Resilty token issuer client ID"
    )
    auth_service_client_secret: SecretStr = Field(
        ..., description="Resilty token issuer client secret"
    )

    # Control plane hosts
    control_plane_api_host: str = Field(
        ..., description="Base URL for the control plane API"
    )

    # Task intervals (in seconds)
    heartbeat_interval: int = Field(
        10, ge=10, description="Interval between heartbeat signals to the control plane"
    )
    runner_interval: int = Field(
        5, ge=5, description="Interval for executing queued resiliency suites"
    )
    resiliency_suite_poll_interval: int = Field(
        10,
        ge=10,
        description="Interval for polling the control plane for new resiliency suites",
    )

    # For discovery
    namespaces: Annotated[list[str], NoDecode] = Field(default_factory=list)

    # Config version from the control plane. This is not same as app_version.
    # This is needed to inform user if they need to redeploy the app
    # if any configuration changes in the control plane.
    config_version: str = Field(
        ..., description="Version or hash of the deployed agent configuration"
    )

    @field_validator("namespaces", mode="before")
    @classmethod
    def parse_namespaces(cls, value: str) -> List[str]:
        if not isinstance(value, str):
            raise ConfigError(
                "RESILTY_AGENT_NAMESPACES must be a comma-separated string"
            )

        namespaces = [ns.strip() for ns in value.split(",") if ns.strip()]

        if not namespaces:
            raise ConfigError(
                "RESILTY_AGENT_NAMESPACES must contain at least one namespace"
            )

        return namespaces

    @property
    def app_version(self) -> str:
        """Version of the installed resilience-agent package."""
        return _APP_VERSION
