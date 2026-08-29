from pathlib import Path

import numpy as np

from services.pipeline.dataset import build_feature_frame, read_source_csv, stage_raw_contacts, strip_audit_columns
from services.pipeline.feature_registry import load_feature_registry
from services.pipeline.modeling import build_decile_summary, build_ranked_scores, candidate_models


REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = REPO_ROOT / "data" / "raw" / "bank-full.csv"


def test_stage_and_feature_build_preserve_full_row_count():
    raw = read_source_csv(DATASET_PATH).head(250)
    staged = stage_raw_contacts(raw)
    curated = build_feature_frame(staged)

    assert len(staged) == len(raw)
    assert len(curated) == len(raw)
    assert curated["contact_id"].is_unique
    assert set(curated["subscribed"].unique()) <= {0, 1}
    assert curated["month_number"].between(1, 12).all()


def test_feature_build_discards_database_audit_columns():
    raw = read_source_csv(DATASET_PATH).head(20)
    staged = stage_raw_contacts(raw)
    staged["loaded_at"] = "2026-08-29T00:00:00Z"

    curated = build_feature_frame(staged)

    assert "loaded_at" not in curated.columns


def test_strip_audit_columns_removes_raw_and_curated_timestamps():
    frame = stage_raw_contacts(read_source_csv(DATASET_PATH).head(5))
    frame["loaded_at"] = "2026-08-29T00:00:00Z"
    frame["feature_built_at"] = "2026-08-29T00:01:00Z"

    stripped = strip_audit_columns(frame)

    assert "loaded_at" not in stripped.columns
    assert "feature_built_at" not in stripped.columns


def test_candidate_model_fits_real_sample_without_duration():
    raw = read_source_csv(DATASET_PATH).head(800)
    staged = stage_raw_contacts(raw)
    curated = build_feature_frame(staged)
    registry = load_feature_registry(REPO_ROOT / "config" / "feature_registry.yml")
    model = candidate_models(registry)["logistic_regression"]

    model.fit(curated.loc[:, list(registry.training_columns)], curated["subscribed"])
    probabilities = model.predict_proba(curated.loc[:, list(registry.training_columns)])[:, 1]

    assert len(probabilities) == len(curated)
    assert np.all((probabilities >= 0.0) & (probabilities <= 1.0))


def test_decile_outputs_cover_entire_population():
    raw = read_source_csv(DATASET_PATH).head(1000)
    staged = stage_raw_contacts(raw)
    curated = build_feature_frame(staged)
    ranked = build_ranked_scores(
        curated.loc[:, ["contact_id", "customer_code", "job", "subscribed"]],
        np.linspace(0.999, 0.001, len(curated)),
        "subscribed",
    )
    deciles = build_decile_summary(ranked, "subscribed")

    assert ranked["decile"].between(1, 10).all()
    assert len(deciles) == 10
    assert int(deciles["prospects"].sum()) == len(curated)
    assert (deciles["lift"] >= 0).all()
