from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DecisionResult:
    customers: pd.DataFrame
    expected_conversions: float
    actual_conversions: int
    expected_cost: float
    expected_revenue: float
    roi: float
    precision: float
    recall: float
    lift: float


def build_decision(
    scores: pd.DataFrame,
    capacity: int,
    contact_cost: float,
    customer_value: float,
) -> DecisionResult:
    if capacity <= 0:
        raise ValueError("capacity must be positive")
    if scores.empty:
        raise ValueError("scores must not be empty")

    selected = (
        scores.sort_values("propensity_score", ascending=False)
        .head(min(capacity, len(scores)))
        .reset_index(drop=True)
    )
    selected["priority_rank"] = range(1, len(selected) + 1)
    expected_conversions = float(selected["propensity_score"].sum())
    actual_conversions = int(selected["actual_subscribed"].sum())
    expected_cost = float(len(selected) * contact_cost)
    expected_revenue = float(expected_conversions * customer_value)
    roi = (expected_revenue - expected_cost) / expected_cost if expected_cost else 0.0
    precision = actual_conversions / len(selected) if len(selected) else 0.0
    total_positives = int(scores["actual_subscribed"].sum())
    recall = actual_conversions / total_positives if total_positives else 0.0
    baseline = float(scores["actual_subscribed"].mean())
    lift = precision / baseline if baseline else 0.0

    return DecisionResult(
        customers=selected,
        expected_conversions=round(expected_conversions, 4),
        actual_conversions=actual_conversions,
        expected_cost=round(expected_cost, 2),
        expected_revenue=round(expected_revenue, 2),
        roi=round(roi, 4),
        precision=round(precision, 4),
        recall=round(recall, 4),
        lift=round(lift, 4),
    )
