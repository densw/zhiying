from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

import joblib
import mlflow
from mlflow import MlflowClient
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier
from sqlalchemy.engine import Engine

from services.pipeline.dataset import strip_audit_columns
from services.pipeline.db import append_table_contents, clear_selected_models, delete_run_outputs, fetch_frame
from services.pipeline.feature_registry import FeatureRegistry, load_feature_registry
from services.pipeline.schemas import validate_curated
from services.pipeline.settings import PipelineSettings


@dataclass(frozen=True)
class ModelBundle:
    run_id: str
    model_name: str
    feature_version: str
    training_columns: tuple[str, ...]
    model_relative_path: str
    trained_at: str


def build_preprocessor(registry: FeatureRegistry) -> ColumnTransformer:
    numeric = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric, list(registry.numeric_features)),
            ("categorical", categorical, list(registry.categorical_features)),
        ]
    )


def candidate_models(registry: FeatureRegistry) -> dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline(
            [
                ("preprocessor", build_preprocessor(registry)),
                (
                    "model",
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=1500,
                        random_state=42,
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("preprocessor", build_preprocessor(registry)),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=300,
                        min_samples_leaf=5,
                        class_weight="balanced_subsample",
                        n_jobs=-1,
                        random_state=42,
                    ),
                ),
            ]
        ),
        "xgboost": Pipeline(
            [
                ("preprocessor", build_preprocessor(registry)),
                (
                    "model",
                    XGBClassifier(
                        n_estimators=300,
                        max_depth=4,
                        learning_rate=0.05,
                        subsample=0.85,
                        colsample_bytree=0.85,
                        min_child_weight=5,
                        scale_pos_weight=7.55,
                        objective="binary:logistic",
                        eval_metric="logloss",
                        n_jobs=-1,
                        random_state=42,
                    ),
                ),
            ]
        ),
    }


def choose_threshold(y_true: pd.Series, probabilities: np.ndarray) -> float:
    precision, recall, thresholds = precision_recall_curve(y_true, probabilities)
    beta_sq = 4.0
    scores = (1.0 + beta_sq) * precision * recall / (beta_sq * precision + recall + 1e-12)
    best_index = int(np.nanargmax(scores[:-1]))
    return float(thresholds[best_index])


def compute_metrics(
    model_name: str,
    y_true: pd.Series,
    probabilities: np.ndarray,
) -> tuple[dict[str, float | str], np.ndarray]:
    threshold = choose_threshold(y_true, probabilities)
    predictions = (probabilities >= threshold).astype(int)
    metrics = {
        "model_name": model_name,
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 6),
        "pr_auc": round(float(average_precision_score(y_true, probabilities)), 6),
        "accuracy": round(float(accuracy_score(y_true, predictions)), 6),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_true, predictions)), 6),
        "precision": round(float(precision_score(y_true, predictions, zero_division=0)), 6),
        "recall": round(float(recall_score(y_true, predictions, zero_division=0)), 6),
        "f1": round(float(f1_score(y_true, predictions, zero_division=0)), 6),
        "log_loss": round(float(log_loss(y_true, probabilities, labels=[0, 1])), 6),
        "brier_score": round(float(brier_score_loss(y_true, probabilities)), 6),
        "threshold": round(float(threshold), 6),
        "confusion_matrix_json": json.dumps(confusion_matrix(y_true, predictions).tolist()),
        "classification_report_text": classification_report(
            y_true,
            predictions,
            digits=4,
            zero_division=0,
        ),
    }
    return metrics, predictions


def feature_importance(model: Pipeline) -> pd.DataFrame:
    feature_names = model.named_steps["preprocessor"].get_feature_names_out()
    estimator = model.named_steps["model"]
    if hasattr(estimator, "feature_importances_"):
        values = estimator.feature_importances_
    else:
        values = np.abs(estimator.coef_[0])
    return (
        pd.DataFrame({"feature": feature_names, "importance": values})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


def build_ranked_scores(
    frame: pd.DataFrame,
    probabilities: np.ndarray,
    target_column: str,
) -> pd.DataFrame:
    ranked = frame.copy()
    ranked["propensity_score"] = probabilities
    ranked = ranked.sort_values("propensity_score", ascending=False).reset_index(drop=True)
    ranked["rank"] = np.arange(1, len(ranked) + 1)
    ranked["population_share"] = ranked["rank"] / len(ranked)
    ranked["decile"] = np.ceil(ranked["population_share"] * 10).clip(upper=10).astype(int)
    ranked["priority_tier"] = np.select(
        [
            ranked["propensity_score"] >= ranked["propensity_score"].quantile(0.90),
            ranked["propensity_score"] >= ranked["propensity_score"].quantile(0.70),
        ],
        ["high", "medium"],
        default="low",
    )
    ranked["cumulative_responders"] = ranked[target_column].cumsum()
    total_responders = max(int(ranked[target_column].sum()), 1)
    baseline_rate = max(float(ranked[target_column].mean()), 1e-12)
    ranked["cumulative_capture_rate"] = ranked["cumulative_responders"] / total_responders
    ranked["cumulative_response_rate"] = ranked["cumulative_responders"] / ranked["rank"]
    ranked["cumulative_lift"] = ranked["cumulative_response_rate"] / baseline_rate
    return ranked


def build_decile_summary(ranked: pd.DataFrame, target_column: str) -> pd.DataFrame:
    baseline_rate = float(ranked[target_column].mean())
    return (
        ranked.groupby("decile", as_index=False)
        .agg(
            prospects=("contact_id", "count"),
            subscribers=(target_column, "sum"),
            response_rate=(target_column, "mean"),
            average_score=("propensity_score", "mean"),
            cumulative_capture_rate=("cumulative_capture_rate", "max"),
            cumulative_lift=("cumulative_lift", "max"),
        )
        .assign(lift=lambda table: table["response_rate"] / baseline_rate)
    )


def normalize_experiment_id(experiment_id: str | int) -> int:
    return int(experiment_id)


def ensure_experiment(settings: PipelineSettings) -> int:
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    client = MlflowClient(tracking_uri=settings.mlflow_tracking_uri)
    experiment = client.get_experiment_by_name(settings.mlflow_experiment_name)
    if experiment:
        return normalize_experiment_id(experiment.experiment_id)
    return normalize_experiment_id(client.create_experiment(
        name=settings.mlflow_experiment_name,
        artifact_location=settings.mlflow_experiment_artifact_location,
    ))


def load_curated_training_frame(engine: Engine, registry: FeatureRegistry) -> pd.DataFrame:
    frame = strip_audit_columns(fetch_frame(
        engine,
        f"SELECT * FROM {registry.source_table} ORDER BY {registry.entity_key}",
    ))
    registry.validate_training_columns(tuple(frame.columns))
    return validate_curated(frame)


def save_bundle_manifest(settings: PipelineSettings, bundle: ModelBundle) -> None:
    manifest_path = settings.models_dir / "latest_model.json"
    manifest_path.write_text(
        json.dumps(asdict(bundle), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_bundle_manifest(settings: PipelineSettings) -> ModelBundle:
    manifest_path = settings.models_dir / "latest_model.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return ModelBundle(
        run_id=payload["run_id"],
        model_name=payload["model_name"],
        feature_version=payload["feature_version"],
        training_columns=tuple(payload["training_columns"]),
        model_relative_path=payload["model_relative_path"],
        trained_at=payload["trained_at"],
    )


def train_models(settings: PipelineSettings, engine: Engine) -> dict[str, object]:
    settings.ensure_runtime_dirs()
    registry = load_feature_registry(settings.registry_path)
    curated = load_curated_training_frame(engine, registry)
    experiment_id = ensure_experiment(settings)
    x_train, x_test, y_train, y_test = train_test_split(
        curated.loc[:, list(registry.training_columns)],
        curated.loc[:, registry.target_column],
        test_size=0.25,
        random_state=42,
        stratify=curated.loc[:, registry.target_column],
    )

    training_records: list[dict[str, object]] = []
    latest_bundle: ModelBundle | None = None

    for model_name, pipeline in candidate_models(registry).items():
        with mlflow.start_run(experiment_id=experiment_id, run_name=model_name) as run:
            pipeline.fit(x_train, y_train)
            probabilities = pipeline.predict_proba(x_test)[:, 1]
            metrics, predictions = compute_metrics(model_name, y_test, probabilities)

            run_dir = settings.artifacts_dir / run.info.run_id
            model_dir = settings.models_dir / run.info.run_id
            report_dir = settings.reports_dir / run.info.run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            model_dir.mkdir(parents=True, exist_ok=True)
            report_dir.mkdir(parents=True, exist_ok=True)

            evaluation = build_ranked_scores(
                curated.loc[
                    x_test.index,
                    list(dict.fromkeys((registry.entity_key, *registry.score_columns, registry.target_column))),
                ],
                probabilities,
                registry.target_column,
            )
            deciles = build_decile_summary(evaluation, registry.target_column)
            importance = feature_importance(pipeline)

            evaluation_path = report_dir / "evaluation_predictions.csv"
            deciles_path = report_dir / "decile_performance.csv"
            importance_path = report_dir / "feature_importance.csv"
            metrics_path = report_dir / "metrics.json"
            report_path = report_dir / "classification_report.txt"
            model_path = model_dir / "model.joblib"

            evaluation.to_csv(evaluation_path, index=False)
            deciles.to_csv(deciles_path, index=False)
            importance.to_csv(importance_path, index=False)
            metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
            report_path.write_text(metrics["classification_report_text"], encoding="utf-8")
            joblib.dump(pipeline, model_path)

            mlflow.log_params(
                {
                    "model_name": model_name,
                    "feature_version": registry.version,
                    "training_rows": len(x_train),
                    "test_rows": len(x_test),
                    "feature_count": len(registry.training_columns),
                    "leakage_guard": "duration_excluded",
                }
            )
            mlflow.log_metrics(
                {
                    key: value
                    for key, value in metrics.items()
                    if isinstance(value, float)
                }
            )
            mlflow.log_artifacts(str(report_dir), artifact_path="reports")
            mlflow.sklearn.log_model(pipeline, artifact_path="model")

            training_records.append(
                {
                    "run_id": run.info.run_id,
                    "experiment_name": settings.mlflow_experiment_name,
                    "model_name": model_name,
                    "feature_version": registry.version,
                    "selected_model": False,
                    "training_rows": len(x_train),
                    "test_rows": len(x_test),
                    "threshold": metrics["threshold"],
                    "roc_auc": metrics["roc_auc"],
                    "pr_auc": metrics["pr_auc"],
                    "accuracy": metrics["accuracy"],
                    "balanced_accuracy": metrics["balanced_accuracy"],
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1": metrics["f1"],
                    "log_loss": metrics["log_loss"],
                    "brier_score": metrics["brier_score"],
                    "confusion_matrix_json": metrics["confusion_matrix_json"],
                    "classification_report_text": metrics["classification_report_text"],
                    "mlflow_tracking_uri": settings.mlflow_tracking_uri,
                    "mlflow_model_uri": f"runs:/{run.info.run_id}/model",
                    "model_artifact_path": str(model_path.relative_to(settings.repo_root)),
                    "report_artifact_path": str(report_dir.relative_to(settings.repo_root)),
                    "trained_at": datetime.now(timezone.utc),
                }
            )

    best_record = max(training_records, key=lambda item: float(item["pr_auc"]))
    for record in training_records:
        if record["run_id"] == best_record["run_id"]:
            record["selected_model"] = True
            latest_bundle = ModelBundle(
                run_id=str(record["run_id"]),
                model_name=str(record["model_name"]),
                feature_version=str(record["feature_version"]),
                training_columns=registry.training_columns,
                model_relative_path=str(record["model_artifact_path"]),
                trained_at=datetime.now(timezone.utc).isoformat(),
            )

    clear_selected_models(engine)
    append_table_contents(engine, "ml.training_runs", pd.DataFrame(training_records))
    if latest_bundle is None:
        raise RuntimeError("No model bundle was selected.")
    save_bundle_manifest(settings, latest_bundle)
    return {
        "selected_run_id": latest_bundle.run_id,
        "selected_model": latest_bundle.model_name,
        "pr_auc": best_record["pr_auc"],
        "roc_auc": best_record["roc_auc"],
        "tracking_uri": settings.mlflow_tracking_uri,
    }


def score_latest_model(settings: PipelineSettings, engine: Engine) -> dict[str, object]:
    settings.ensure_runtime_dirs()
    registry = load_feature_registry(settings.registry_path)
    bundle = load_bundle_manifest(settings)
    curated = load_curated_training_frame(engine, registry)
    model_path = settings.repo_root / bundle.model_relative_path
    model = joblib.load(model_path)

    probabilities = model.predict_proba(curated.loc[:, list(bundle.training_columns)])[:, 1]
    ranked = build_ranked_scores(
        curated.loc[
            :,
            list(dict.fromkeys((registry.entity_key, *registry.score_columns, registry.target_column))),
        ],
        probabilities,
        registry.target_column,
    )
    ranked["run_id"] = bundle.run_id
    ranked["model_name"] = bundle.model_name
    ranked["scored_at"] = datetime.now(timezone.utc)

    deciles = build_decile_summary(ranked, registry.target_column)
    deciles["run_id"] = bundle.run_id

    score_output = ranked[
        [
            "run_id",
            "contact_id",
            "customer_code",
            "model_name",
            "scored_at",
            registry.target_column,
            "propensity_score",
            "priority_tier",
            "decile",
            "cumulative_capture_rate",
            "cumulative_lift",
        ]
    ].rename(columns={registry.target_column: "actual_subscribed"})

    decile_output = deciles[
        [
            "run_id",
            "decile",
            "prospects",
            "subscribers",
            "response_rate",
            "average_score",
            "cumulative_capture_rate",
            "cumulative_lift",
            "lift",
        ]
    ]

    delete_run_outputs(engine, bundle.run_id)
    append_table_contents(engine, "ml.model_scores", score_output)
    append_table_contents(engine, "ml.model_score_deciles", decile_output)

    run_report_dir = settings.reports_dir / bundle.run_id
    run_report_dir.mkdir(parents=True, exist_ok=True)
    score_output.to_csv(run_report_dir / "full_population_scores.csv", index=False)
    decile_output.to_csv(run_report_dir / "full_population_deciles.csv", index=False)

    return {
        "run_id": bundle.run_id,
        "model_name": bundle.model_name,
        "scored_rows": len(score_output),
        "top_decile_lift": round(float(decile_output.loc[decile_output["decile"] == 1, "lift"].iloc[0]), 6),
    }
