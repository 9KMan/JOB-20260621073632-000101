// src/services/decision_engine.py
"""Decision Engine for routing matches to appropriate actions."""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.matching import Match, MatchDecision, MatchLine
from app.models.user import User
from app.config import settings


class DecisionEngine:
    """
    Decision Engine for routing matches to appropriate actions.
    
    Routing logic:
    - CONFIRMED + High Score (>= threshold) → AUTO_APPROVE
    - CONFIRMED + Medium Score (>= threshold) → HUMAN_REVIEW
    - REJECTED → DISPUTE
    
    Human confirmations feed back into future matching (learning loop).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def make_decision(
        self,
        total_score: Decimal,
        line_level_score: Decimal,
        amount_score: Decimal,
        variance_percentage: Decimal,
        has_delivery_note: bool = True,
    ) -> Dict[str, Any]:
        """
        Make a match decision based on scores and thresholds.
        """
        auto_approve_threshold = Decimal(str(settings.MATCH_THRESHOLD_AUTO_APPROVE))
        pending_threshold = Decimal(str(settings.MATCH_THRESHOLD_PENDING_REVIEW))

        decision = {
            "status": "PENDING",
            "decision": "HUMAN_REVIEW",
            "reason": "",
            "requires_review": True,
            "auto_approved": False,
        }

        # Check for rejection conditions
        if amount_score < Decimal("0.30"):
            decision["status"] = "REJECTED"
            decision["decision"] = "DISPUTE"
            decision["reason"] = "Significant amount variance detected"
            decision["requires_review"] = True
            return decision

        if line_level_score < Decimal("0.40"):
            decision["status"] = "REJECTED"
            decision["decision"] = "DISPUTE"
            decision["reason"] = "Poor line-level match"
            decision["requires_review"] = False
            return decision

        # High confidence: Auto-approve
        if total_score >= auto_approve_threshold and has_delivery_note:
            decision["status"] = "CONFIRMED"
            decision["decision"] = "AUTO_APPROVE"
            decision["reason"] = f"High confidence match (score: {total_score:.2%})"
            decision["requires_review"] = False
            decision["auto_approved"] = True
            return decision

        # Medium confidence: Require human review
        if total_score >= pending_threshold:
            decision["status"] = "CONFIRMED"
            decision["decision"] = "HUMAN_REVIEW"
            decision["reason"] = f"Match requires verification (score: {total_score:.2%})"
            decision["requires_review"] = True
            return decision

        # Low confidence but not rejected: Flag for review
        decision["status"] = "PENDING"
        decision["decision"] = "HUMAN_REVIEW"
        decision["reason"] = f"Match below threshold, manual review required (score: {total_score:.2%})"
        decision["requires_review"] = True
        return decision

    async def apply_decision(
        self,
        match_id: str,
        user_id: str,
        new_decision: str,
        notes: Optional[str] = None,
    ) -> Optional[Match]:
        """
        Apply a human decision to a match.
        """
        # Get the match
        query = select(Match).where(Match.id == match_id)
        result = await self.db.execute(query)
        match = result.scalar_one_or_none()

        if match is None:
            return None

        previous_decision = match.decision

        # Update match with decision
        match.decision = new_decision
        match.reviewed_by = user_id
        match.reviewed_at = datetime.utcnow()
        match.review_notes = notes

        # Update status based on decision
        if new_decision == "AUTO_APPROVE":
            match.status = "CONFIRMED"
        elif new_decision == "DISPUTE":
            match.status = "REJECTED"
        else:
            match.status = "CONFIRMED"

        # Record decision for learning loop
        decision_record = MatchDecision(
            match_id=match_id,
            previous_decision=previous_decision,
            new_decision=new_decision,
            reviewed_by=user_id,
            review_notes=notes,
        )
        self.db.add(decision_record)

        await self.db.commit()
        await self.db.refresh(match)

        return match

    async def batch_approve(
        self,
        match_ids: List[str],
        user_id: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Batch approve multiple matches.
        """
        approved = []
        failed = []

        for match_id in match_ids:
            try:
                match = await self.apply_decision(
                    match_id=match_id,
                    user_id=user_id,
                    new_decision="AUTO_APPROVE",
                    notes=notes or "Batch approved",
                )
                if match:
                    approved.append(match_id)
                else:
                    failed.append({"match_id": match_id, "reason": "Match not found"})
            except Exception as e:
                failed.append({"match_id": match_id, "reason": str(e)})

        return {
            "approved_count": len(approved),
            "failed_count": len(failed),
            "approved": approved,
            "failed": failed,
        }

    async def get_decision_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get statistics on match decisions for analysis.
        """
        from sqlalchemy import func

        # Base query for matches
        base_filter = []
        if start_date:
            base_filter.append(Match.created_at >= start_date)
        if end_date:
            base_filter.append(Match.created_at <= end_date)

        # Count by decision
        decision_query = select(
            Match.decision,
            func.count(Match.id).label("count"),
        ).where(*base_filter) if base_filter else select(
            Match.decision,
            func.count(Match.id).label("count"),
        )

        result = await self.db.execute(decision_query.group_by(Match.decision))
        decision_counts = {row.decision: row.count for row in result.all()}

        # Average score by decision
        avg_score_query = select(
            Match.decision,
            func.avg(Match.total_score).label("avg_score"),
        ).where(*base_filter) if base_filter else select(
            Match.decision,
            func.avg(Match.total_score).label("avg_score"),
        )

        result = await self.db.execute(avg_score_query.group_by(Match.decision))
        avg_scores = {row.decision: float(row.avg_score) if row.avg_score else 0.0 for row in result.all()}

        return {
            "total_matches": sum(decision_counts.values()),
            "by_decision": decision_counts,
            "average_score_by_decision": avg_scores,
            "auto_approve_rate": (
                decision_counts.get("AUTO_APPROVE", 0) / sum(decision_counts.values()) * 100
                if sum(decision_counts.values()) > 0
                else 0.0
            ),
            "human_review_rate": (
                decision_counts.get("HUMAN_REVIEW", 0) / sum(decision_counts.values()) * 100
                if sum(decision_counts.values()) > 0
                else 0.0
            ),
            "dispute_rate": (
                decision_counts.get("DISPUTE", 0) / sum(decision_counts.values()) * 100
                if sum(decision_counts.values()) > 0
                else 0.0
            ),
        }

    async def learn_from_historical_decisions(
        self,
        user_id: str,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Analyze historical decisions to suggest threshold adjustments.
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

        # Get recent decisions
        query = select(MatchDecision).where(
            MatchDecision.created_at >= cutoff_date
        ).order_by(MatchDecision.created_at.desc())

        result = await self.db.execute(query)
        decisions = result.scalars().all()

        # Analyze patterns
        auto_approved_after_review = 0
        disputed_auto_approvals = 0

        for decision in decisions:
            if decision.previous_decision == "HUMAN_REVIEW" and decision.new_decision == "AUTO_APPROVE":
                auto_approved_after_review += 1
            elif decision.previous_decision == "AUTO_APPROVE" and decision.new_decision == "DISPUTE":
                disputed_auto_approvals += 1

        # Get corresponding matches for score analysis
        match_query = select(Match).where(
            Match.created_at >= cutoff_date
        ).order_by(Match.created_at.desc())
        match_result = await self.db.execute(match_query)
        matches = match_result.scalars().all()

        # Calculate score thresholds from successful auto-approvals
        successful_auto_approvals = [
            m.total_score for m in matches
            if m.decision == "AUTO_APPROVE" and m.status == "CONFIRMED"
        ]

        suggestions = {
            "analysis_period_days": lookback_days,
            "total_decisions_analyzed": len(decisions),
            "upgraded_to_approve": auto_approved_after_review,
            "downgraded_to_dispute": disputed_auto_approvals,
        }

        if successful_auto_approvals:
            min_successful_score = min(successful_auto_approvals)
            avg_successful_score = sum(successful_auto_approvals) / len(successful_auto_approvals)

            suggestions["recommended_auto_approve_threshold"] = float(min_successful_score)
            suggestions["avg_successful_auto_approve_score"] = float(avg_successful_score)
            suggestions["threshold_adjustment_needed"] = (
                float(min_successful_score) < settings.MATCH_THRESHOLD_AUTO_APPROVE
            )

        return suggestions
