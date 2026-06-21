// src/models/enums.py
"""Enumeration types for the application."""
import enum


class DocumentStatus(str, enum.Enum):
    """Status of a document (PO, Invoice, Delivery Note)."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    DISPUTED = "disputed"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class MatchStatus(str, enum.Enum):
    """Status of a match record."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class MatchDecision(str, enum.Enum):
    """Decision outcome for a match."""
    AUTO_APPROVED = "auto_approved"
    HUMAN_REVIEW = "human_review"
    DISPUTED = "disputed"


class DocumentType(str, enum.Enum):
    """Type of document."""
    PURCHASE_ORDER = "purchase_order"
    INVOICE = "invoice"
    DELIVERY_NOTE = "delivery_note"


class UserRole(str, enum.Enum):
    """User roles in the system."""
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    APPROVER = "approver"
    VIEWER = "viewer"
