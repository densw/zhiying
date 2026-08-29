from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class FeatureRegistry:
    version: str
    entity_key: str
    target_column: str
    raw_table: str
    source_table: str
    numeric_features: tuple[str, ...]
    categorical_features: tuple[str, ...]
    excluded_features: tuple[str, ...]
    score_columns: tuple[str, ...]

    @property
    def training_columns(self) -> tuple[str, ...]:
        columns = (*self.numeric_features, *self.categorical_features)
        overlap = set(columns).intersection(self.excluded_features)
        if overlap:
            raise ValueError(f"Excluded features cannot be trained: {sorted(overlap)}")
        return columns

    def validate_training_columns(self, available_columns: list[str] | tuple[str, ...]) -> None:
        missing = set(self.training_columns).difference(available_columns)
        if missing:
            raise ValueError(f"Training columns missing from dataset: {sorted(missing)}")
        leaked = set(self.excluded_features).intersection(self.training_columns)
        if leaked:
            raise ValueError(f"Leakage guard failed for features: {sorted(leaked)}")


def load_feature_registry(path: Path) -> FeatureRegistry:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return FeatureRegistry(
        version=str(payload["version"]),
        entity_key=str(payload["entity_key"]),
        target_column=str(payload["target_column"]),
        raw_table=str(payload["raw_table"]),
        source_table=str(payload["source_table"]),
        numeric_features=tuple(payload["numeric_features"]),
        categorical_features=tuple(payload["categorical_features"]),
        excluded_features=tuple(payload["excluded_features"]),
        score_columns=tuple(payload["score_columns"]),
    )
