// src/app/core/exceptions.py
"""Custom exceptions for the application."""
from typing import Any


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    """Resource not found exception."""

    def __init__(self, resource: str, identifier: str | int):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            status_code=404,
            details={"resource": resource, "identifier": str(identifier)},
        )


class DuplicateException(AppException):
    """Duplicate resource exception."""

    def __init__(self, resource: str, field: str, value: str):
        super().__init__(
            message=f"{resource} with {field} '{value}' already exists",
            status_code=409,
            details={"resource": resource, "field": field, "value": value},
        )


class ValidationException(AppException):
    """Validation error exception."""

    def __init__(self, message: str, errors: list[dict] | None = None):
        super().__init__(
            message=message,
            status_code=422,
            details={"errors": errors or []},
        )


class AuthenticationException(AppException):
    """Authentication error exception."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=401,
        )


class AuthorizationException(AppException):
    """Authorization error exception."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            status_code=403,
        )


class MatchingException(AppException):
    """Matching engine error exception."""

    def __init__(self, message: str, invoice_id: str | None = None):
        super().__init__(
            message=message,
            status_code=422,
            details={"invoice_id": invoice_id},
        )


class BalanceException(AppException):
    """Balance resolution error exception."""

    def __init__(self, message: str, po_id: str | None = None):
        super().__init__(
            message=message,
            status_code=422,
            details={"purchase_order_id": po_id},
        )
