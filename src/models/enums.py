// src/models/enums.py
"""SQLAlchemy enum types."""
import enum

from sqlalchemy import Enum as SQLEnum


class MatchStatus(enum.Enum):
    """Status of a match operation."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class MatchDecision(enum.Enum):
    """Decision outcome for a match."""
    AUTO_APPROVE = "auto_approve"
    HUMAN_REVIEW = "human_review"
    DISPUTE = "dispute"


class DocumentStatus(enum.Enum):
    """Status of a document (PO, Invoice, Delivery Note)."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class MatchType(enum.Enum):
    """Type of matching operation."""
    INVOICE_PO = "invoice_po"
    DELIVERY_PO = "delivery_po"
    INVOICE_DELIVERY = "invoice_delivery"
    THREE_WAY = "three_way"


class UserRole(enum.Enum):
    """User roles for authorization."""
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"


# SQLAlchemy enum mappers
match_status_enum = SQLEnum(MatchStatus, name="match_status", create_type=True)
match_decision_enum = SQLEnum(MatchDecision, name="match_decision", create_type=True)
document_status_enum = SQLEnum(DocumentStatus, name="document_status", create_type=True)
match_type_enum = SQLEnum(MatchType, name="match_type", create_type=True)
user_role_enum = SQLEnum(UserRole, name="user_role", create_type=True)
