// src/models/enums.py
"""Enumeration types for the application."""
import enum
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ENUM as PGEnum


class MatchStatus(str, enum.Enum):
    """Status of a match between documents."""
    PENDING = "PENDING"           # Awaiting review
    CONFIRMED = "CONFIRMED"       # Match confirmed
    REJECTED = "REJECTED"         # Match rejected
    AUTO_APPROVED = "AUTO_APPROVED"  # Automatically approved
    DISPUTE = "DISPUTE"           # In dispute


class MatchType(str, enum.Enum):
    """Type of document match."""
    PO_INVOICE = "PO_INVOICE"           # Purchase Order ↔ Invoice
    PO_DELIVERY = "PO_DELIVERY"         # Purchase Order ↔ Delivery Note
    INVOICE_DELIVERY = "INVOICE_DELIVERY"  # Invoice ↔ Delivery Note
    THREE_WAY = "THREE_WAY"             # All three documents matched


class BalanceType(str, enum.Enum):
    """Type of balance entry."""
    INVOICE_BALANCE = "INVOICE_BALANCE"       # Remaining invoice amount
    DELIVERY_BALANCE = "DELIVERY_BALANCE"     # Remaining delivery amount
    PO_BALANCE = "PO_BALANCE"                 # Remaining PO amount


class DocumentStatus(str, enum.Enum):
    """Status of a document."""
    DRAFT = "DRAFT"               # Not yet processed
    OPEN = "OPEN"                 # Open/active
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"  # Some lines matched
    FULLY_MATCHED = "FULLY_MATCHED"          # All lines matched
    CLOSED = "CLOSED"             # Fully processed
    CANCELLED = "CANCELLED"       # Cancelled


class UserRole(str, enum.Enum):
    """User roles for access control."""
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    REVIEWER = "REVIEWER"
    VIEWER = "VIEWER"


# SQLAlchemy enum types for PostgreSQL
match_status_enum = PGEnum(
    MatchStatus,
    name="match_status_enum",
    create_type=True,
    create_constraint=True,
    validate_strings=True
)

match_type_enum = PGEnum(
    MatchType,
    name="match_type_enum",
    create_type=True,
    create_constraint=True,
    validate_strings=True
)

balance_type_enum = PGEnum(
    BalanceType,
    name="balance_type_enum",
    create_type=True,
    create_constraint=True,
    validate_strings=True
)

document_status_enum = PGEnum(
    DocumentStatus,
    name="document_status_enum",
    create_type=True,
    create_constraint=True,
    validate_strings=True
)

user_role_enum = PGEnum(
    UserRole,
    name="user_role_enum",
    create_type=True,
    create_constraint=True,
    validate_strings=True
)
