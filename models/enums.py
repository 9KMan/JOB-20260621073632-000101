"""Enumerations shared across models, schemas, and services."""

from __future__ import annotations

from enum import StrEnum


class DocumentStatus(StrEnum):
    """Lifecycle states for source documents (Invoice, PO, DN)."""

    PENDING = "pending"
    INGESTED = "ingested"
    PROCESSING = "processing"
    MATCHED = "matched"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ERROR = "error"


class MatchLayer(StrEnum):
    """Which matching layer produced a decision."""

    NONE = "none"
    ANCHOR = "anchor"  # Layer 1: PO anchoring
    CASCADE = "cascade"  # Layer 2: line matching cascade
    LEARNING = "learning"  # Layer 3: cross-ref promotion
    MANUAL = "manual"


class DecisionType(StrEnum):
    """Routing decision the engine produced for a line."""

    AUTO_APPROVE = "auto_approve"  # score >= THRESHOLD_HIGH
    ONE_CLICK_REVIEW = "one_click_review"  # score >= THRESHOLD_MID
    EXCEPTION = "exception"  # below THRESHOLD_LOW or no candidate
    NEEDS_REVIEW = "needs_review"  # between LOW and MID
    REJECTED = "rejected"


class ExceptionSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExceptionStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"
