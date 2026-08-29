from services.report_queries import REPORT_QUERIES


def test_report_queries_cover_management_sections():
    assert {"overview", "monthly", "segments", "channels", "campaigns", "model", "capacity", "quality", "recommendations"} == set(REPORT_QUERIES)
    assert all(query.startswith("SELECT") for query in REPORT_QUERIES.values())
