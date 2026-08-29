from services.analytics_queries import ANALYTICS_QUERIES


def test_public_analytics_reads_shared_analytics_marts():
    assert set(ANALYTICS_QUERIES) == {"overview", "monthly", "segments", "channels", "campaigns", "model"}
    assert all("analytics." in query for query in ANALYTICS_QUERIES.values())
