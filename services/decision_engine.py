from __future__ import annotations

import numpy as np
import pandas as pd

MONTH_ORDER = {name: index for index, name in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), start=1)}
TRAINING_COLUMNS = ("age", "balance", "campaign", "pdays", "previous", "month_number", "day", "job", "marital", "education", "default", "housing", "loan", "contact", "poutcome")
REQUIRED_NATIVE_COLUMNS = ("age", "balance", "campaign", "pdays", "previous", "day", "month", "job", "marital", "education", "default", "housing", "loan", "contact", "poutcome")


def align_training_features(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    normalized.columns = [str(column).strip().lower() for column in normalized.columns]
    missing = [column for column in REQUIRED_NATIVE_COLUMNS if column not in normalized.columns]
    if missing:
        raise ValueError(f"新数据缺少字段：{', '.join(missing)}")
    normalized["month_number"] = normalized["month"].astype(str).str.lower().map(MONTH_ORDER)
    if normalized["month_number"].isna().any():
        raise ValueError("month 字段包含无法识别的月份")
    aligned = normalized.loc[:, list(TRAINING_COLUMNS)].copy()
    return aligned


def rank_new_batch(frame: pd.DataFrame) -> pd.DataFrame:
    ranked = frame.sort_values("propensity_score", ascending=False).reset_index(drop=True).copy()
    ranked["priority_rank"] = np.arange(1, len(ranked) + 1)
    ranked["priority_tier"] = np.select(
        [ranked["propensity_score"] >= ranked["propensity_score"].quantile(0.90), ranked["propensity_score"] >= ranked["propensity_score"].quantile(0.70)],
        ["高优先级", "中优先级"],
        default="低优先级",
    )
    ranked["score_decile"] = np.ceil(ranked["priority_rank"] / max(len(ranked) / 10, 1)).clip(upper=10).astype(int)
    channels = ranked["contact"] if "contact" in ranked.columns else pd.Series("cellular", index=ranked.index)
    ranked["recommended_channel"] = np.where(channels.eq("cellular"), "手机", "电话")
    return ranked
