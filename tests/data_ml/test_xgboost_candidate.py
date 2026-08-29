from pathlib import Path

from services.pipeline.feature_registry import load_feature_registry
from services.pipeline.modeling import candidate_models


def test_candidate_models_include_xgboost_with_shared_features():
    registry = load_feature_registry(Path("config/feature_registry.yml"))
    candidates = candidate_models(registry)
    assert {"logistic_regression", "random_forest", "xgboost"} == set(candidates)
    assert list(candidates["xgboost"].named_steps["preprocessor"].transformers[0][2]) == list(registry.numeric_features)
