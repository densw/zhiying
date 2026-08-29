from services.monitoring_explanation import build_explanation


def test_build_explanation_contains_chinese_business_interpretation():
    result = build_explanation({"rows": 100, "quality_score": 1.0, "drift_columns": ["age"]})
    assert "数据质量" in result["title"]
    assert "客户年龄" in result["summary"]
    assert result["status"] == "需关注"
