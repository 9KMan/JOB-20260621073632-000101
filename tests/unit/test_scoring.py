python
// tests/unit/test_scoring.py
"""Unit tests for scoring service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from api.schemas import LineDecisionOut
from models.enums import DecisionType, MatchLayer
from services.scoring import aggregate_overall_score, best_layer, route_decision


def _ld(score: float, *, has_po: bool = True, layer: MatchLayer = MatchLayer.CASCADE):
    return LineDecisionOut(
        invoice_line_id=uuid.uuid4(),
        purchase_order_line_id=uuid.uuid4() if has_po else None,
        score=score,
        decision=DecisionType.NEEDS_REVIEW,
        layer=layer,
        reasons=[],
    )


def test_aggregate_overall_score_empty_returns_zero():
    assert aggregate_overall_score([]) == 0.0


def test_aggregate_overall_score_averages_line_scores():
    rows = [_ld(80), _ld(60), _ld(100)]
    assert aggregate_overall_score(rows) == 80.0


def test_route_decision_high_score_auto_approves(settings):
    rows = [_ld(95), _ld(98)]
    assert route_decision(aggregate_overall_score(rows), rows) == DecisionType.AUTO_APPROVE


def test_route_decision_mid_score_one_click_review(settings):
    rows = [_ld(82)]
    score = aggregate_overall_score(rows)
    assert route_decision(score, rows) == DecisionType.ONE_CLICK_REVIEW


def test_route_decision_low_score_with_candidates_needs_review(settings):
    rows = [_ld(65, has_po=True)]
    score = aggregate_overall_score(rows)
    assert route_decision(score, rows) == DecisionType.NEEDS_REVIEW


def test_route_decision_low_score_without_candidates_exception(settings):
    rows = [_ld(40, has_po=False)]
    score = aggregate_overall_score(rows)
    assert route_decision(score, rows) == DecisionType.EXCEPTION


def test_best_layer_picks_most_specific():
    rows = [
        _ld(80, layer=MatchLayer.CASCADE),
        _ld(70, layer=MatchLayer.LEARNING),
    ]
    assert best_layer(rows) == MatchLayer.LEARNING


def test_best_layer_returns_none_when_empty():
    assert best_layer([]) == MatchLayer.NONE

