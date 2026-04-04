from typing import Any, Dict, Optional


class APIRequestError(Exception):
    """Raised when an API request returns a non-success HTTP response."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.context = context or {}


class ResiliencySuiteExecutionError(Exception):

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.context = context or {}


class AuthServiceError(Exception):
    pass
