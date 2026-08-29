from services.orchestration.graph import ASSET_SEQUENCE


def test_asset_sequence_covers_the_complete_business_lineage():
    assert ASSET_SEQUENCE == (
        "raw_bank_data",
        "validated_bank_data",
        "analytics_marts",
        "feature_table",
        "trained_model",
        "model_evaluation",
        "customer_scores",
        "campaign_simulation",
        "business_report",
        "monitoring_report",
    )
