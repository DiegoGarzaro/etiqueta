"""Domain-level exceptions mapped to HTTP responses at the API edge."""


class ServiceError(Exception):
    """Base class for expected domain errors.

    Attributes:
        status_code (int): HTTP status to return for this error.
    """

    status_code: int = 400


class NotFoundError(ServiceError):
    """Raised when a requested resource does not exist."""

    status_code = 404


class ConflictError(ServiceError):
    """Raised when an operation conflicts with current state."""

    status_code = 409


class ValidationError(ServiceError):
    """Raised when input is structurally valid but semantically wrong."""

    status_code = 422


class UnauthorizedError(ServiceError):
    """Raised when credentials (the access PIN) are missing or wrong."""

    status_code = 401


class TooManyAttemptsError(ServiceError):
    """Raised when login attempts are temporarily locked out."""

    status_code = 429
