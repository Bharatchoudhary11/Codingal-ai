from __future__ import annotations

from core.services.recommender import RecommendationResult, score_candidate


def test_score_candidate_is_deterministic():
    params = {
        "progress_percent": 20.0,
        "recency_gap_days": 7.0,
        "tag_alignment": 0.5,
        "hint_rate": 1.0,
    }
    first = score_candidate(**params)
    second = score_candidate(**params)
    assert first.score == second.score
    assert first.confidence == second.confidence
    assert first.explanation == second.explanation
    assert [feature.key for feature in first.features] == [
        feature.key for feature in second.features
    ]


def test_score_candidate_feature_shapes():
    result = score_candidate(50.0, 0.0, 1.0, 0.0)
    assert isinstance(result, RecommendationResult)
    assert result.score >= 0
    feature_map = {feature.key: feature for feature in result.features}
    assert "progress_gap" in feature_map
    assert feature_map["progress_gap"].normalized_value <= 1.0
    assert result.explanation
    assert 0.0 <= result.confidence <= 1.0
