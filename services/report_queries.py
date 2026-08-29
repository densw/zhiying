REPORT_QUERIES = {
    "overview": "SELECT * FROM analytics.executive_overview",
    "monthly": "SELECT * FROM analytics.monthly_conversion ORDER BY month_number",
    "segments": "SELECT * FROM analytics.customer_segment_performance ORDER BY conversion_rate DESC",
    "channels": "SELECT * FROM analytics.channel_performance ORDER BY conversion_rate DESC",
    "campaigns": "SELECT * FROM analytics.campaign_performance ORDER BY contacts DESC",
    "model": "SELECT * FROM analytics.model_quality_overview ORDER BY score_decile",
    "capacity": "SELECT * FROM analytics.capacity_scenarios ORDER BY capacity",
    "quality": "SELECT * FROM analytics.data_quality_overview",
    "recommendations": "SELECT * FROM analytics.recommendations ORDER BY priority",
}
