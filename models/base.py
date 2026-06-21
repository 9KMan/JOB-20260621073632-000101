// models/base.py
"""Base model with common fields."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr


class BaseModel:
    """Base model with common fields."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate __tablename__ from class name."""
        import re
        name = cls.__name__
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
