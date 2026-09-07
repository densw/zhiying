import pandas as pd

from services.experiment_views import latest_candidates, latest_split_comparison


def test_latest_candidates_returns_one_latest_run_per_model():
    runs = pd.DataFrame(
        {
            "model_name": ["random_forest", "logistic_regression", "random_forest"],
            "trained_at": pd.to_datetime(["2026-01-02", "2026-01-02", "2026-01-01"]),
        }
    )
    latest = latest_candidates(runs)
    assert latest["model_name"].tolist() == ["random_forest", "logistic_regression"]
    assert len(latest) == 2


def test_latest_split_comparison_keeps_one_run_per_model_and_strategy():
    runs = pd.DataFrame(
        {
            "model_name": ["xgboost", "xgboost", "xgboost", "random_forest"],
            "split_strategy": ["random", "time", "random", "time"],
            "trained_at": pd.to_datetime(
                ["2026-02-02", "2026-02-02", "2026-01-01", "2026-02-02"]
            ),
        }
    )

    comparison = latest_split_comparison(runs)

    assert len(comparison) == 3
    assert comparison[["model_name", "split_strategy"]].values.tolist() == [
        ["xgboost", "random"],
        ["xgboost", "time"],
        ["random_forest", "time"],
    ]
