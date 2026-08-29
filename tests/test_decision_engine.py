import pandas as pd

from services.decision_engine import align_training_features, rank_new_batch


def test_align_training_features_maps_native_month_and_drops_leaky_duration():
    raw = pd.DataFrame({"age": [35], "balance": [1200], "campaign": [1], "pdays": [-1], "previous": [0], "day": [4], "month": ["may"], "job": ["management"], "marital": ["single"], "education": ["tertiary"], "default": ["no"], "housing": ["yes"], "loan": ["no"], "contact": ["cellular"], "poutcome": ["unknown"], "duration": [180]})
    aligned = align_training_features(raw)
    assert aligned.loc[0, "month_number"] == 5
    assert "duration" not in aligned.columns


def test_rank_new_batch_orders_probability_and_assigns_priority():
    frame = pd.DataFrame({"customer_code": ["NEW-1", "NEW-2"], "propensity_score": [0.2, 0.8]})
    ranked = rank_new_batch(frame)
    assert ranked["customer_code"].tolist() == ["NEW-2", "NEW-1"]
    assert ranked["priority_rank"].tolist() == [1, 2]
    assert ranked["priority_tier"].tolist() == ["高优先级", "低优先级"]
