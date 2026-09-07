from __future__ import annotations

import pandas as pd


def latest_candidates(runs: pd.DataFrame) -> pd.DataFrame:
    if "split_strategy" in runs.columns:
        runs = runs[runs["split_strategy"].fillna("random") == "random"]
    return (
        runs.sort_values("trained_at", ascending=False)
        .drop_duplicates("model_name", keep="first")
        .reset_index(drop=True)
    )


def latest_split_comparison(runs: pd.DataFrame) -> pd.DataFrame:
    return (
        runs.sort_values("trained_at", ascending=False)
        .drop_duplicates(["model_name", "split_strategy"], keep="first")
        .reset_index(drop=True)
    )
