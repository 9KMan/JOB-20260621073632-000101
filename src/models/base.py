// src/models/base.py
"""
FinaRo AP Automation Core Engine
Base Model with Common Fields
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model with common fields for all entities.
    Uses UUID as primary key and includes audit timestamps.
    """
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    
    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True
    )
    
    is_deleted = Column(
        "is_deleted",
        default=False,
        nullable=False,
        index=True
    )
    
    def soft_delete(self) -> None:
        """Mark the record as soft deleted."""
        self.is_deleted = True
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def get_by_id(cls, session, record_id: uuid.UUID):
        """Get a record by its ID."""
        return session.query(cls).filter(
            cls.id == record_id,
            cls.is_deleted == False
        ).first()
