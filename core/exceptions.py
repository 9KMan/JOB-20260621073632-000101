# core/exceptions.py
"""
Custom exception classes for the AP Automation Engine.
"""

from __future__ import annotations


class APAutomationError(Exception):
    """Base exception for all AP Automation errors."""

    def __init__(self, message: str, code: str | None = None, details: dict | None = None):
        self.message = message
        self.code = code or "AP_ERROR"
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


# ─── Data / Model Errors ─────────────────────────────────────────────────────


class EntityNotFoundError(APAutomationError):
    """Raised when a requested entity (invoice, PO, etc.) is not found."""

    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            message=f"{entity_type} with id '{entity_id}' not found",
            code=f"NOT_FOUND_{entity_type.upper()}",
            details={"entity_type": entity_type, "entity_id": str(entity_id)},
        )


class DuplicateEntityError(APAutomationError):
    """Raised when attempting to create a duplicate entity."""

    def __init__(self, entity_type: str, identifier: str):
        super().__init__(
            message=f"{entity_type} with identifier '{identifier}' already exists",
            code=f"DUPLICATE_{entity_type.upper()}",
            details={"entity_type": entity_type, "identifier": identifier},
        )


class InvalidStateError(APAutomationError):
    """Raised when an entity is in an invalid state for the requested operation."""

    def __init__(self, entity_type: str, current_state: str, required_state: str):
        super().__init__(
            message=f"{entity_type} is in state '{current_state}', expected '{required_state}'",
            code="INVALID_STATE",
            details={
                "entity_type": entity_type,
                "current_state": current_state,
                "required_state": required_state,
            },
        )


# ─── Matching Errors ──────────────────────────────────────────────────────────


class MatchingError(APAutomationError):
    """Base exception for matching engine errors."""

    def __init__(self, message: str, invoice_id: str | None = None, po_id: str | None = None):
        super().__init__(
            message=message,
            code="MATCHING_ERROR",
            details={"invoice_id": str(invoice_id) if invoice_id else None,
                     "po_id": str(po_id) if po_id else None},
        )


class NoAnchorFoundError(MatchingError):
    """Raised when no purchase order anchor can be found for an invoice."""

    def __init__(self, invoice_id: str, reason: str = "No matching PO found"):
        super().__init__(
            message=f"Cannot anchor invoice '{invoice_id}': {reason}",
            invoice_id=invoice_id,
        )
        self.code = "NO_ANCHOR_FOUND"


class AmbiguousAnchorError(MatchingError):
    """Raised when multiple potential PO anchors are found."""

    def __init__(self, invoice_id: str, candidates: list[str]):
        super().__init__(
            message=f"Invoice '{invoice_id}' matches multiple POs",
            invoice_id=invoice_id,
        )
        self.code = "AMBIGUOUS_ANCHOR"
        self.details["candidates"] = candidates


class CascadeError(MatchingError):
    """Raised when line-level matching cascade fails."""

    def __init__(self, invoice_id: str, line_number: int, reason: str):
        super().__init__(
            message=f"Line {line_number} cascade failed: {reason}",
            invoice_id=invoice_id,
        )
        self.code = "CASCADE_ERROR"
        self.details["line_number"] = line_number


class InsufficientBalanceError(APAutomationError):
    """Raised when PO balance is insufficient for matching."""

    def __init__(self, po_id: str, required: float, available: float):
        super().__init__(
            message=f"PO '{po_id}' has insufficient balance: required={required}, available={available}",
            code="INSUFFICIENT_BALANCE",
            details={
                "po_id": str(po_id),
                "required": required,
                "available": available,
            },
        )


# ─── API Errors ───────────────────────────────────────────────────────────────


class ValidationAPIError(APAutomationError):
    """Raised when API request validation fails."""

    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Validation error on '{field}': {message}",
            code="VALIDATION_ERROR",
            details={"field": field},
        )


class AuthenticationError(APAutomationError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, code="AUTH_ERROR")


class AuthorizationError(APAutomationError):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message=message, code="AUTHORIZATION_ERROR")


# ─── Service Errors ───────────────────────────────────────────────────────────


class LearningError(APAutomationError):
    """Raised when learning loop processing fails."""

    def __init__(self, message: str, record_id: str | None = None):
        super().__init__(
            message=message,
            code="LEARNING_ERROR",
            details={"record_id": str(record_id) if record_id else None},
        )


class BalanceUpdateError(APAutomationError):
    """Raised when balance ledger update fails."""

    def __init__(self, po_id: str, reason: str):
        super().__init__(
            message=f"Balance update failed for PO '{po_id}': {reason}",
            code="BALANCE_UPDATE_ERROR",
            details={"po_id": str(po_id)},
        )
