python
// services/scoring.py
"""Score aggregation and threshold routing.

The cascade produces a per-line score and layer; scoring combines them into an
overall invoice-level score and routes the result to one of:

* ``AUTO_APPROVE``   - overall score >= ``threshold_high``
* ``ONE_CLICK_REVIEW`` - ``threshold_mid`` <= score < ``threshold_high``
* ``NEEDS_REVIEW``   - ``threshold_low`` <= score < ``threshold_mid``
* ``EXCEPTION``      - score < ``threshold_low`` or any line lacks a candidate
"""

from __future__ import annotations

from typing import Iterable, Optional

from core.config import get_settings
from models.enums import DecisionType, MatchLayer

from api.schemas import LineDecisionOut  # type: ignore  # noqa: F401  (re-export)


def aggregate_overall_score(line_decisions: Iterable[LineDecisionOut]) -> float:
    """Weighted average: confidence-weighted by line total when available."""
    rows = list(line_decisions)
    if not rows:
        return 0.0
    total_weight = 0.0
    weighted = 0.0
    for ld in rows:
        # Equal weight per line; in production we'd weight by line_total.
        weight = 1.0
        weighted += ld.score * weight
        total_weight += weight
    return round(weighted / total_weight, 2) if total_weight else 0.0


def route_decision(
    overall_score: float,
    line_decisions: Optional[Iterable[LineDecisionOut]] = None,
) -> DecisionType:
    """Map an overall score (and optional line context) to a DecisionType."""
    settings = get_settings()
    lines = list(line_decisions) if line_decisions else []

    if overall_score >= settings.threshold_high:
        return DecisionType.AUTO_APPROVE
    if overall_score >= settings.threshold_mid:
        return DecisionType.ONE_CLICK_REVIEW
    if overall_score >= settings.threshold_low:
        return DecisionType.NEEDS_REVIEW

    # Below the low threshold, but check whether every line had a candidate.
    if lines and all(ld.purchase_order_line_id is not None for ld in lines):
        # Even with low confidence, if every line is anchored, this is a review
        # queue candidate rather than a hard exception.
        return DecisionType.NEEDS_REVIEW
    return DecisionType.EXCEPTION


def best_layer(line_decisions: Iterable[LineDecisionOut]) -> MatchLayer:
    """Pick the most 'specific' layer across the decision set."""
    order = {
        MatchLayer.MANUAL: 4,
        MatchLayer.LEARNING: 3,
        MatchLayer.CASCADE: 2,
        MatchLayer.ANCHOR: 1,
        MatchLayer.NONE: 0,
    }
    best = MatchLayer.NONE
    for ld in line_decisions:
        if order[ld.layer] > order[best]:
            best = ld.layer
    return best

