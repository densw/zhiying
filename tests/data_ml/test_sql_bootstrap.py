from pathlib import Path


def test_reserved_default_column_is_quoted_in_bootstrap_sql():
    sql = Path("warehouse/sql/bootstrap.sql").read_text(encoding="utf-8")
    assert '"default" VARCHAR(8)' in sql


def test_pipeline_pins_pandera_compatible_multimethod():
    requirements = Path("services/pipeline/requirements.txt").read_text(encoding="utf-8")
    assert "multimethod<2" in requirements
