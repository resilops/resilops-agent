from agent.exceptions import (
    APIRequestError,
    AuthServiceError,
    ConfigError,
    NotLeaderError,
)


def test_api_request_error_stores_context_and_status_code():
    error = APIRequestError("boom", status_code=422, context={"field": "value"})

    assert str(error) == "boom"
    assert error.status_code == 422
    assert error.context == {"field": "value"}


def test_domain_exceptions_are_plain_exceptions():
    assert isinstance(AuthServiceError("auth"), Exception)
    assert isinstance(ConfigError("config"), Exception)
    assert isinstance(NotLeaderError("leader"), Exception)
