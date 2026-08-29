from services.pipeline.modeling import normalize_experiment_id


def test_normalize_experiment_id_returns_integer_for_mlflow_postgres():
    assert normalize_experiment_id("1") == 1
    assert normalize_experiment_id(2) == 2
