from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import os


@dataclass(frozen=True)
class PipelineSettings:
    repo_root: Path
    dataset_path: Path
    registry_path: Path
    sql_bootstrap_path: Path
    artifacts_dir: Path
    models_dir: Path
    reports_dir: Path
    database_url: str
    mlflow_tracking_uri: str
    mlflow_experiment_name: str
    mlflow_experiment_artifact_location: str | None

    @classmethod
    def from_env(cls) -> "PipelineSettings":
        repo_root = Path(__file__).resolve().parents[2]
        return cls(
            repo_root=repo_root,
            dataset_path=Path(
                os.getenv(
                    "PIPELINE_DATASET_PATH",
                    repo_root / "data" / "raw" / "customer_campaign_full.csv",
                )
            ),
            registry_path=Path(
                os.getenv(
                    "PIPELINE_FEATURE_REGISTRY",
                    repo_root / "config" / "feature_registry.yml",
                )
            ),
            sql_bootstrap_path=Path(
                os.getenv(
                    "PIPELINE_SQL_BOOTSTRAP",
                    repo_root / "warehouse" / "sql" / "bootstrap.sql",
                )
            ),
            artifacts_dir=Path(
                os.getenv(
                    "PIPELINE_ARTIFACT_DIR",
                    repo_root / "runtime" / "artifacts",
                )
            ),
            models_dir=Path(
                os.getenv(
                    "PIPELINE_MODEL_DIR",
                    repo_root / "runtime" / "models",
                )
            ),
            reports_dir=Path(
                os.getenv(
                    "PIPELINE_REPORT_DIR",
                    repo_root / "runtime" / "reports",
                )
            ),
            database_url=os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg://postgres:postgres@localhost:5432/zhiying",
            ),
            mlflow_tracking_uri=os.getenv(
                "MLFLOW_TRACKING_URI",
                "http://localhost:5000",
            ),
            mlflow_experiment_name=os.getenv(
                "MLFLOW_EXPERIMENT_NAME",
                "customer-propensity-training",
            ),
            mlflow_experiment_artifact_location=os.getenv(
                "MLFLOW_EXPERIMENT_ARTIFACT_LOCATION"
            ),
        )

    def override(
        self,
        *,
        dataset_path: str | None = None,
        database_url: str | None = None,
        mlflow_tracking_uri: str | None = None,
        mlflow_experiment_name: str | None = None,
    ) -> "PipelineSettings":
        return replace(
            self,
            dataset_path=Path(dataset_path) if dataset_path else self.dataset_path,
            database_url=database_url or self.database_url,
            mlflow_tracking_uri=mlflow_tracking_uri or self.mlflow_tracking_uri,
            mlflow_experiment_name=mlflow_experiment_name
            or self.mlflow_experiment_name,
        )

    def ensure_runtime_dirs(self) -> None:
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
