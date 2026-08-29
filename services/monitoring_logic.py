from __future__ import annotations

import pandas as pd


POST_CONTACT_COLUMNS = {"duration", "contact_duration_minutes"}


def prepare_monitoring_frames(
    frame: pd.DataFrame,
    reference_share: float = 0.7,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 < reference_share < 1:
        raise ValueError("reference_share must be between zero and one")
    if len(frame) < 2:
        raise ValueError("at least two rows are required")

    safe = frame.drop(columns=[column for column in POST_CONTACT_COLUMNS if column in frame], errors="ignore")
    safe = safe.sort_values("contact_id").reset_index(drop=True)
    boundary = min(max(round(len(safe) * reference_share), 1), len(safe) - 1)
    return safe.iloc[:boundary].copy(), safe.iloc[boundary:].copy()
