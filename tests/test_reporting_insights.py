import pandas as pd

from services.reporting_insights import build_report_insights


def test_build_report_insights_turns_marts_into_business_story():
    result = build_report_insights(
        pd.Series({"total_customers": 100, "conversions": 12, "conversion_rate": 0.12}),
        pd.DataFrame({"score_decile": [1, 2], "actual_conversions": [6, 3], "lift": [5.0, 2.5]}),
        pd.DataFrame({"capacity": [10], "expected_conversions": [4.0], "expected_roi": [2.0]}),
        pd.DataFrame({"channel_name": ["手机", "电话"], "conversion_rate": [0.16, 0.1]}),
        pd.DataFrame({"customer_segment": ["高潜", "大众"], "conversion_rate": [0.2, 0.1]}),
    )
    assert result["baseline_rate"] == 0.12
    assert result["top_decile_lift"] == 5.0
    assert result["top_decile_capture"] == 0.5
    assert result["best_channel"] == "手机"
    assert result["best_segment"] == "高潜"
    assert result["decision_message"]
