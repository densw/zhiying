import pandas as pd

from services.experiment_views import latest_candidates


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
