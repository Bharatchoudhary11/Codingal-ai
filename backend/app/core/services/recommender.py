"""Deterministic recommendation scoring utilities."""
from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Callable, Dict, Iterable, List


def _clamp(value: float, *, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


@dataclass(frozen=True)
class FeatureDefinition:
    """Metadata describing how a particular feature contributes to the score."""

    key: str
    weight: float
    normalizer: Callable[[float], float]
    formatter: Callable[[float], str]


@dataclass(frozen=True)
class FeatureResult:
    """Concrete contribution of a feature to a recommendation score."""

    key: str
    raw_value: float
    normalized_value: float
    weight: float
    contribution: float
    description: str


@dataclass(frozen=True)
class RecommendationResult:
    score: float
    confidence: float
    explanation: str
    features: List[FeatureResult]

    def as_dict(self) -> Dict[str, float]:
        return {
            feature.key: feature.raw_value for feature in self.features
        }


FEATURES: Iterable[FeatureDefinition] = (
    FeatureDefinition(
        key="progress_gap",
        weight=0.4,
        normalizer=lambda progress_percent: _clamp((100.0 - progress_percent) / 100.0),
        formatter=lambda progress_percent: f"{100 - round(progress_percent)}% of lessons still to go",
    ),
    FeatureDefinition(
        key="recency_gap",
        weight=0.25,
        normalizer=lambda gap_days: _clamp(gap_days / 14.0),
        formatter=lambda gap_days: (
            "No activity yet" if gap_days == float("inf") else f"Last activity {gap_days:.1f} days ago"
        ),
    ),
    FeatureDefinition(
        key="tag_alignment",
        weight=0.2,
        normalizer=lambda alignment: _clamp(alignment),
        formatter=lambda alignment: f"Covers {round(alignment * 100)}% of focus areas",
    ),
    FeatureDefinition(
        key="support_need",
        weight=0.15,
        normalizer=lambda hint_rate: _clamp(hint_rate / 3.0),
        formatter=lambda hint_rate: f"Average of {hint_rate:.1f} hints used per attempt",
    ),
)


def _build_feature_results(inputs: Dict[str, float]) -> List[FeatureResult]:
    results: List[FeatureResult] = []
    for feature in FEATURES:
        raw_value = inputs.get(feature.key)
        if raw_value is None:
            continue
        normalized = feature.normalizer(raw_value)
        contribution = feature.weight * normalized
        description = feature.formatter(raw_value)
        results.append(
            FeatureResult(
                key=feature.key,
                raw_value=raw_value,
                normalized_value=normalized,
                weight=feature.weight,
                contribution=contribution,
                description=description,
            )
        )
    return results


def _explain(features: List[FeatureResult]) -> str:
    positive_features = [f for f in features if f.contribution > 0]
    if not positive_features:
        return "Insufficient engagement data; showing default suggestion."
    ordered = sorted(positive_features, key=lambda item: item.contribution, reverse=True)
    parts = [feature.description for feature in ordered[:3]]
    return "; ".join(parts)


def _confidence_from_score(score: float) -> float:
    # Smooth logistic curve centred near 0.5.
    return _clamp(1.0 / (1.0 + exp(-4.0 * (score - 0.5))))


def score_candidate(
    progress_percent: float,
    recency_gap_days: float,
    tag_alignment: float,
    hint_rate: float,
) -> RecommendationResult:
    inputs = {
        "progress_gap": progress_percent,
        "recency_gap": recency_gap_days,
        "tag_alignment": tag_alignment,
        "support_need": hint_rate,
    }
    features = _build_feature_results(inputs)
    score = sum(feature.contribution for feature in features)
    confidence = _confidence_from_score(score)
    explanation = _explain(features)
    return RecommendationResult(score=score, confidence=confidence, explanation=explanation, features=features)


__all__ = [
    "FeatureDefinition",
    "FeatureResult",
    "RecommendationResult",
    "score_candidate",
]
