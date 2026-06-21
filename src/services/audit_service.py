// src/services/audit_service.py
"""Audit service for logging all changes."""
import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.models.audit_log import AuditLog
from src.models.base import BaseModel


class AuditService:
    """Service for audit logging."""

    def __init__(self, db: Session):
        """Initialize audit service."""
        self.db = db

    def log_create(
        self,
        entity: BaseModel,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLog:
        """Log entity creation."""
        return self._create_log(
            action="CREATE",
            entity_type=entity.__class__.__name__,
            entity_id=entity.id,
            user_id=user_id,
            username=username,
            new_values=json.dumps(entity.to_dict()),
            request_id=request_id,
        )

    def log_update(
        self,
        entity: BaseModel,
        changes: dict,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLog:
        """Log entity update."""
        old_values = entity.to_dict()
        return self._create_log(
            action="UPDATE",
            entity_type=entity.__class__.__name__,
            entity_id=entity.id,
            user_id=user_id,
            username=username,
            old_values=json.dumps(old_values),
            new_values=json.dumps({**old_values, **changes}),
            changes=json.dumps(changes),
            request_id=request_id,
        )

    def log_delete(
        self,
        entity: BaseModel,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLog:
        """Log entity deletion."""
        return self._create_log(
            action="DELETE",
            entity_type=entity.__class__.__name__,
            entity_id=entity.id,
            user_id=user_id,
            username=username,
            old_values=json.dumps(entity.to_dict()),
            request_id=request_id,
        )

    def log_action(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        description: Optional[str] = None,
        severity: str = "INFO",
        request_id: Optional[str] = None,
    ) -> AuditLog:
        """Log a custom action."""
        return self._create_log(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            username=username,
            description=description,
            severity=severity,
            request_id=request_id,
        )

    def _create_log(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        old_values: Optional[str] = None,
        new_values: Optional[str] = None,
        changes: Optional[str] = None,
        description: Optional[str] = None,
        severity: str = "INFO",
        request_id: Optional[str] = None,
    ) -> AuditLog:
        """Create audit log entry."""
        log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            username=username,
            old_values=old_values,
            new_values=new_values,
            changes=changes,
            description=description,
            severity=severity,
            request_id=request_id,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_logs_for_entity(self, entity_type: str, entity_id: str) -> list[AuditLog]:
        """Get all audit logs for a specific entity."""
        return (
            self.db.query(AuditLog)
            .filter(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(AuditLog.created_at.desc())
            .all()
        )

    def get_logs_by_user(self, user_id: str, limit: int = 100) -> list[AuditLog]:
        """Get all audit logs for a specific user."""
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_logs_by_action(self, action: str, limit: int = 100) -> list[AuditLog]:
        """Get all audit logs for a specific action."""
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.action == action)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
