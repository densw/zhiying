from pathlib import Path

from services.pipeline.feature_registry import load_feature_registry


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_duration_is_excluded_from_training_features():
    registry = load_feature_registry(REPO_ROOT / "config" / "feature_registry.yml")
    assert "duration" not in registry.training_columns
    assert "contact_duration_minutes" not in registry.training_columns
    assert "duration" in registry.excluded_features


def test_training_columns_cover_expected_business_features():
    registry = load_feature_registry(REPO_ROOT / "config" / "feature_registry.yml")
    assert registry.target_column == "subscribed"
    assert registry.entity_key == "contact_id"
    assert registry.training_columns == (
        "age",
        "balance",
        "campaign",
        "pdays",
        "previous",
        "month_number",
        "day",
        "job",
        "marital",
        "education",
        "default",
        "housing",
        "loan",
        "contact",
        "poutcome",
    )
