// src/services/decision_engine.py
"""Decision engine for routing matches to appropriate actions."""
from dataclasses import dataclass

from src.app.config import get_settings
from src.api.schemas.matching import MatchDecision


class DecisionEngine:
    """
    Decision engine that routes matches based on scores and criteria.
    
    Routes:
    - CONFIRMED + High Score → AUTO_APPROVE
    - PENDING Score → HUMAN_REVIEW
    - REJECTED + Low Score → DISPUTE
    """

    def __init__(self):
        self.settings = get_settings()
        self.threshold_approve = self.settings.MATCHING_THRESHOLD_AUTO_APPROVE
        self.threshold_pending = self.settings.MATCHING_THRESHOLD_PENDING

    def determine_decision(
        self,
        score: float,
        has_warnings: bool,
        balance_status: str,
        human_confirmations: int = 0
    ) -> MatchDecision:
        """
        Determine the decision for a match based on score and criteria.
        
        Args:
            score: Overall match score (0.0 - 1.0)
            has_warnings: Whether there are warnings in the match
            balance_status: Current balance status
            human_confirmations: Number of human confirmations for this match set
        
        Returns:
            MatchDecision with status, action, and reason
        """
        # High score, no warnings, balanced → Auto approve
        if score >= self.threshold_approve and not has_warnings and balance_status == "BALANCED":
            return MatchDecision(
                status="AUTO_APPROVED",
                action="AUTO_APPROVE",
                reason="Match score exceeds threshold with no warnings and balanced amounts",
                confidence=score,
                requires_approval=False,
                approver_roles=None
            )

        # High score with warnings → Pending review with warnings
        if score >= self.threshold_approve and has_warnings:
            return MatchDecision(
                status="PENDING_REVIEW",
                action="HUMAN_REVIEW",
                reason=f"Match score meets threshold but has {len([])} warnings requiring review",
                confidence=score,
                requires_approval=True,
                approver_roles=["APPROVER", "SENIOR_APPROVER"]
            )

        # Medium score → Pending review
        if score >= self.threshold_pending:
            return MatchDecision(
                status="PENDING_REVIEW",
                action="HUMAN_REVIEW",
                reason="Match score in pending range - manual review required",
                confidence=score,
                requires_approval=True,
                approver_roles=["APPROVER"]
            )

        # Low score or unbalanced → Reject/Dispute
        if balance_status == "UNBALANCED":
            return MatchDecision(
                status="REJECTED",
                action="DISPUTE",
                reason="Document amounts are unbalanced - requires dispute resolution",
                confidence=score,
                requires_approval=True,
                approver_roles=["DISPUTE_RESOLUTION", "MANAGER"]
            )

        # Low score without human confirmations
        if human_confirmations == 0:
            return MatchDecision(
                status="REJECTED",
                action="DISPUTE",
                reason="Match score below threshold without human confirmation",
                confidence=score,
                requires_approval=True,
                approver_roles=["DISPUTE_RESOLUTION"]
            )

        # Low score with partial human confirmations
        confirmation_ratio = human_confirmations / max(1, 3)  # Assuming 3 lines need confirmation
        if confirmation_ratio >= 0.5:
            return MatchDecision(
                status="PENDING_REVIEW",
                action="HUMAN_REVIEW",
                reason=f"Partial human confirmations ({human_confirmations}) - escalate to supervisor",
                confidence=score + (confirmation_ratio * 0.2),
                requires_approval=True,
                approver_roles=["SENIOR_APPROVER"]
            )

        return MatchDecision(
            status="REJECTED",
            action="DISPUTE",
            reason="Low match score with insufficient human confirmations",
            confidence=score,
            requires_approval=True,
            approver_roles=["DISPUTE_RESOLUTION", "MANAGER"]
        )

    def calculate_approval_levels(
        self,
        score: float,
        amount: float
    ) -> list[str]:
        """
        Determine required approval levels based on score and amount.
        
        Args:
            score: Match score
            amount: Transaction amount
        
        Returns:
            List of required approval roles
        """
        levels = []

        # Always requires basic approval
        levels.append("APPROVER")

        # Higher amounts need more approval
        if amount > 10000:
            levels.append("SENIOR_APPROVER")
        if amount > 50000:
            levels.append("MANAGER")
        if amount > 100000:
            levels.append("DIRECTOR")

        # Lower scores need more approval
        if score < 0.8:
            if "SENIOR_APPROVER" not in levels:
                levels.append("SENIOR_APPROVER")
        if score < 0.6:
            if "MANAGER" not in levels:
                levels.append("MANAGER")

        return levels

    def suggest_review_priority(
        self,
        score: float,
        age_hours: int,
        amount: float
    ) -> str:
        """
        Suggest review priority for manual review queue.
        
        Returns:
            Priority level: CRITICAL, HIGH, MEDIUM, LOW
        """
        # Age-based priority
        if age_hours > 72:
            age_priority = "HIGH"
        elif age_hours > 24:
            age_priority = "MEDIUM"
        else:
            age_priority = "LOW"

        # Amount-based priority
        if amount > 50000:
            amount_priority = "CRITICAL"
        elif amount > 10000:
            amount_priority = "HIGH"
        elif amount > 1000:
            amount_priority = "MEDIUM"
        else:
            amount_priority = "LOW"

        # Score-based priority (inverse)
        if score < 0.5:
            score_priority = "CRITICAL"
        elif score < 0.7:
            score_priority = "HIGH"
        elif score < 0.85:
            score_priority = "MEDIUM"
        else:
            score_priority = "LOW"

        # Return highest priority
        priorities = [age_priority, amount_priority, score_priority]
        if "CRITICAL" in priorities:
            return "CRITICAL"
        elif "HIGH" in priorities:
            return "HIGH"
        elif "MEDIUM" in priorities:
            return "MEDIUM"
        return "LOW"
