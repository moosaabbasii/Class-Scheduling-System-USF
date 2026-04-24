class ApplicationError(Exception):
    """Base application exception with a FastAPI-friendly status code."""

    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ApplicationError):
    status_code = 404


class ConflictError(ApplicationError):
    status_code = 409


class ValidationError(ApplicationError):
    status_code = 422


class LockedScheduleError(ApplicationError):
    status_code = 409


class AuthorizationError(ApplicationError):
    status_code = 403
