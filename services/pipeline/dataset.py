from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy.engine import Engine

from services.pipeline.db import fetch_frame, replace_table_contents
from services.pipeline.schemas import validate_curated, validate_staged_raw
from services.pipeline.settings import PipelineSettings


MONTH_ORDER = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

AUDIT_COLUMNS = ("loaded_at", "feature_built_at")


def strip_audit_columns(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.drop(columns=list(AUDIT_COLUMNS), errors="ignore").copy()


def read_source_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";")


def age_band(age: pd.Series) -> pd.Series:
    return pd.cut(
        age,
        bins=[17, 29, 39, 49, 59, 120],
        labels=["18-29", "30-39", "40-49", "50-59", "60+"],
    ).astype("string")


def balance_band(balance: pd.Series) -> pd.Series:
    return pd.cut(
        balance,
        bins=[-np.inf, 0, 500, 1500, 5000, np.inf],
        labels=["<=0", "1-500", "501-1,500", "1,501-5,000", "5,000+"],
    ).astype("string")


def stage_raw_contacts(raw: pd.DataFrame) -> pd.DataFrame:
    frame = raw.copy()
    frame.columns = [column.strip().lower() for column in frame.columns]
    frame.insert(0, "contact_id", np.arange(1, len(frame) + 1, dtype=int))
    frame.insert(1, "customer_code", "KH" + frame["contact_id"].astype(str).str.zfill(6))
    return validate_staged_raw(frame)


def build_feature_frame(staged: pd.DataFrame) -> pd.DataFrame:
    frame = strip_audit_columns(staged)
    frame["subscribed"] = frame["y"].eq("yes").astype(int)
    frame["month_number"] = frame["month"].map(MONTH_ORDER).astype(int)
    frame["month_name"] = frame["month"].str.upper()
    frame["age_band"] = age_band(frame["age"])
    frame["balance_band"] = balance_band(frame["balance"])
    frame["has_prior_contact"] = frame["pdays"].ne(-1).astype(int)
    frame["contact_duration_minutes"] = (frame["duration"] / 60.0).round(2)
    frame["campaign_intensity"] = pd.cut(
        frame["campaign"],
        bins=[0, 1, 2, 4, np.inf],
        labels=["1 contact", "2 contacts", "3-4 contacts", "5+ contacts"],
    ).astype("string")
    curated = frame.drop(columns=["y"])
    return validate_curated(curated)


def import_raw_dataset(settings: PipelineSettings, engine: Engine) -> pd.DataFrame:
    if not settings.dataset_path.exists():
        raise FileNotFoundError(f"Missing dataset at {settings.dataset_path}")
    staged = stage_raw_contacts(read_source_csv(settings.dataset_path))
    replace_table_contents(engine, "raw.customer_campaign_contacts", staged)
    return staged


def build_curated_dataset(engine: Engine) -> pd.DataFrame:
    staged = fetch_frame(engine, "SELECT * FROM raw.customer_campaign_contacts ORDER BY contact_id")
    curated = build_feature_frame(staged)
    replace_table_contents(engine, "curated.customer_features", curated)
    return curated
