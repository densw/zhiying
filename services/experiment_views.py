from __future__ import annotations

import pandas as pd


def latest_candidates(runs: pd.DataFrame) -> pd.DataFrame:
    return (
        runs.sort_values("trained_at", ascending=False)
        .drop_duplicates("model_name", keep="first")
        .reset_index(drop=True)
    )
