// src/services/decision_engine.py
import logging
from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from src.models.models import MatchRecord, MatchStatus, DocumentStatus
from src.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DecisionEngine:
    """
    Decision Engine - Routes matches to appropriate action.
    
    Decision Matrix:
    - CONFIRMED + HIGH_SCORE → AUTO-APPROVE
    - PENDING + MEDIUM_SCORE → HUMAN_REVIEW
    - REJECTED + LOW_SCORE → DISPUTE
    """

    def __init__(self, db: Session):
        self.db = db
        self.auto_approve_threshold = settings.AUTO_APPROVE_THRESHOLD
        self.human_review_threshold = settings.HUMAN_REVIEW_THRESHOLD

    def evaluate_match(self, match_record: MatchRecord) -> Tuple[str, str]:
        """
        Evaluate a match record and determine the appropriate action.
        
        Returns:
            Tuple of (decision, reason)
        """
        score = float(match_record.total_score)
        variance = float(match_record.variance_amount or 0)
        
        # Check variance tolerance
        variance_tolerance = settings.BALANCE_TOLERANCE_AMOUNT
        
        logger.info(
            f"Evaluating match {match_record.id}: "
            f"score={score:.4f}, variance={variance}"
        )
        
        # Decision logic
        if score >= self.auto_approve_threshold and abs(variance) <= variance_tolerance:
            decision = "AUTO_APPROVE"
            reason = f"High score ({score:.4f}) and within variance tolerance"
        elif score >= self.human_review_threshold:
            decision = "HUMAN_REVIEW"
            reason = f"Medium score ({score:.4f}) requires human verification"
        elif score >= 0.5:
            decision = "HUMAN_REVIEW"
            reason = f"Score {score:.4f} below threshold but above minimum"
        else:
            decision = "REJECT"
            reason = f"Low score ({score:.4f}) indicates significant mismatch"
        
        return decision, reason

    def route_match(
        self,
        match_record: MatchRecord,
        decision: Optional[str] = None,
        reason: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> MatchRecord:
        """
        Route a match to the appropriate handler based on decision.
        
        Updates match record with decision and sets appropriate status.
        """
        if decision is None:
            decision, reason = self.evaluate_match(match_record)
        
        match_record.decision = decision
        match_record.decision_reason = reason
        match_record.decided_at = datetime.utcnow()
        
        if user_id:
            match_record.decided_by = user_id
        
        # Route based on decision
        if decision == "AUTO_APPROVE":
            match_record.status = MatchStatus.AUTO_APPROVED
            match_record.requires_review = False
            self._handle_auto_approve(match_record)
            
        elif decision == "HUMAN_REVIEW":
            match_record.status = MatchStatus.HUMAN_REVIEW
            match_record.requires_review = True
            self._handle_human_review(match_record)
            
        elif decision == "REJECT":
            match_record.status = MatchStatus.REJECTED
            match_record.requires_review = True
            self._handle_reject(match_record)
            
        elif decision == "DISPUTE":
            match_record.status = MatchStatus.DISPUTED
            match_record.requires_review = True
            self._handle_dispute(match_record)
        
        self.db.flush()
        
        logger.info(
            f"Match {match_record.id} routed to {decision}: {reason}"
        )
        
        return match_record

    def process_user_decision(
        self,
        match_record: MatchRecord,
        user_decision: str,
        reviewer_id: str,
        notes: Optional[str] = None,
    ) -> MatchRecord:
        """
        Process a human decision on a match.
        
        Args:
            match_record: The match record to update
            user_decision: One of 'approve', 'reject', 'dispute'
            reviewer_id: ID of the user making the decision
            notes: Optional review notes
        """
        if user_decision == "approve":
            match_record.status = MatchStatus.CONFIRMED
            match_record.decision = "CONFIRMED"
            self._handle_approve(match_record)
            
        elif user_decision == "reject":
            match_record.status = MatchStatus.REJECTED
            match_record.decision = "REJECTED"
            self._handle_reject(match_record)
            
        elif user_decision == "dispute":
            match_record.status = MatchStatus.DISPUTED
            match_record.decision = "DISPUTED"
            self._handle_dispute(match_record)
        
        match_record.decided_by = reviewer_id
        match_record.decided_at = datetime.utcnow()
        match_record.review_notes = notes
        
        self.db.flush()
        
        logger.info(
            f"Match {match_record.id} {match_record.status} by {reviewer_id}"
        )
        
        return match_record

    def _handle_auto_approve(self, match_record: MatchRecord) -> None:
        """Handle auto-approved match."""
        # Update document statuses
        if match_record.po_id:
            po = self.db.query(match_record.__class__).filter_by(id=match_record.po_id).first()
            # Will be handled in balance service
        
        if match_record.invoice_id:
            # Mark invoice for approval workflow
            from src.models.models import Invoice
            invoice = self.db.query(Invoice).filter(Invoice.id == match_record.invoice_id).first()
            if invoice:
                invoice.status = DocumentStatus.APPROVED

    def _handle_human_review(self, match_record: MatchRecord) -> None:
        """Handle match requiring human review."""
        # Update document statuses
        if match_record.invoice_id:
            from src.models.models import Invoice
            invoice = self.db.query(Invoice).filter(Invoice.id == match_record.invoice_id).first()
            if invoice:
                invoice.status = DocumentStatus.PENDING

    def _handle_approve(self, match_record: MatchRecord) -> None:
        """Handle user-approved match."""
        if match_record.invoice_id:
            from src.models.models import Invoice
            invoice = self.db.query(Invoice).filter(Invoice.id == match_record.invoice_id).first()
            if invoice:
                invoice.status = DocumentStatus.APPROVED

    def _handle_reject(self, match_record: MatchRecord) -> None:
        """Handle rejected match."""
        if match_record.invoice_id:
            from src.models.models import Invoice
            invoice = self.db.query(Invoice).filter(Invoice.id == match_record.invoice_id).first()
            if invoice:
                invoice.status = DocumentStatus.REJECTED

    def _handle_dispute(self, match_record: MatchRecord) -> None:
        """Handle disputed match."""
        if match_record.invoice_id:
            from src.models.models import Invoice
            invoice = self.db.query(Invoice).filter(Invoice.id == match_record.invoice_id).first()
            if invoice:
                invoice.status = DocumentStatus.DISPUTED

    def get_pending_reviews(self, limit: int = 100) -> list:
        """Get all matches pending human review."""
        return (
            self.db.query(MatchRecord)
            .filter(
                MatchRecord.status == MatchStatus.HUMAN_REVIEW,
                MatchRecord.requires_review == True,
            )
            .order_by(MatchRecord.created_at.desc())
            .limit(limit)
            .all()
        )
