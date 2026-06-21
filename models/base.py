// models/base.py
"""SQLAlchemy declarative base and shared mixins.

This module provides the Base class that all models inherit from,
along with reusable mixins for common table features like timestamps
and UUID primary keys.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, TypeVar

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    declared_attr,
)


# Type variable for generic model references
ModelType = TypeVar("ModelType", bound=Any)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class.

    All database models should inherit from this class.
    It provides common table arguments and serves as the
    base for all model definitions.

    Example:
        