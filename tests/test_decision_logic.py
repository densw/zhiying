import pandas as pd

from services.decision_logic import build_decision


def test_build_decision_selects_highest_probabilities_and_computes_business_metrics():
    scores = pd.DataFrame(
        {
            "customer_code": ["KH001", "KH002", "KH003"],
            "propensity_score": [0.2, 0.9, 0.6],
            "actual_subscribed": [0, 1, 1],
            "decile": [3, 1, 2],
        }
    )

    result = build_decision(scores, capacity=2, contact_cost=10, customer_value=100)

    assert result.customers["customer_code"].tolist() == ["KH002", "KH003"]
    assert result.expected_conversions == 1.5
    assert result.actual_conversions == 2
    assert result.expected_cost == 20
    assert result.expected_revenue == 150
    assert result.roi == 6.5
    assert result.precision == 1.0
    assert result.recall == 1.0
    assert result.lift == 1.5


def test_build_decision_rejects_invalid_capacity():
    scores = pd.DataFrame({"propensity_score": [0.5], "actual_subscribed": [1]})

    try:
        build_decision(scores, capacity=0, contact_cost=10, customer_value=100)
    except ValueError as error:
        assert "capacity" in str(error)
    else:
        raise AssertionError("capacity=0 must be rejected")
