// src/app/engine/decision_router.py
"""Decision Router - Routes matches to appropriate workflow."""

from typing import Optional

from src.app.config import get_settings
from src.app.models.matching import MatchDecision

settings = get_settings()


class DecisionRouter:
    """
    Decision Router for Match Results
    
    Routes all matches through a decision engine:
    - CONFIRMED → AUTO-APPROVE (score >= auto_approve_threshold)
    - PENDING → HUMAN_REVIEW (score >= human_review_threshold)
    - REJECTED → DISPUTE (score < human_review_threshold)
    
    Human confirmations in the cross-reference table feed back
    into future matching (learning loop).
    """

    def __init__(self):
        """Initialize decision router with thresholds."""
        self.auto_approve_threshold = settings.auto_approve_threshold
        self.human_review_threshold = settings.human_review_threshold

    def route(self, score: float, match_type: str) -> MatchDecision:
        """
        Route a match to the appropriate decision.
        
        Args:
            score: Match score (0.0 to 1.0)
            match_type: Type of matching performed
            
        Returns:
            MatchDecision enum value
        """
        if score >= self.auto_approve_threshold:
            return MatchDecision.CONFIRMED
        elif score >= self.human_review_threshold:
            return MatchDecision.PENDING
        else:
            return MatchDecision.REJECTED

    def get_routing_reason(
        self,
        decision: MatchDecision,
        score: float
    ) -> str:
        """
        Get human-readable reason for the routing decision.
        
        Args:
            decision: The routing decision made
            score: The match score
            
        Returns:
            Explanation string
        """
        if decision == MatchDecision.CONFIRMED:
            return (
                f"Auto-approved: Match score {score:.2%} exceeds "
                f"threshold of {self.auto_approve_threshold:.2%}"
            )
        elif decision == MatchDecision.PENDING:
            return (
                f"Requires human review: Match score {score:.2%} is below "
                f"auto-approve threshold but above review threshold "
                f"({self.human_review_threshold:.2%})"
            )
        else:
            return (
                f"Rejected: Match score {score:.2%} is below "
                f"review threshold of {self.human_review_threshold:.2%}"
            )

    def should_auto_process(self, decision: MatchDecision) -> bool:
        """
        Determine if a decision can be auto-processed.
        
        Args:
            decision: The routing decision
            
        Returns:
            True if auto-processing is possible
        """
        return decision == MatchDecision.CONFIRMED

    def get_workflow_action(self, decision: MatchDecision) -> str:
        """
        Get the workflow action for a decision.
        
        Args:
            decision: The routing decision
            
        Returns:
            Workflow action string
        """
        actions = {
            MatchDecision.CONFIRMED: "AUTO_APPROVE",
            MatchDecision.PENDING: "HUMAN_REVIEW",
            MatchDecision.REJECTED: "DISPUTE"
        }
        return actions.get(decision, "UNKNOWN")
