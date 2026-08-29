from __future__ import annotations

import pandas as pd


def build_report_insights(overview: pd.Series, model: pd.DataFrame, capacity: pd.DataFrame, channels: pd.DataFrame, segments: pd.DataFrame) -> dict[str, object]:
    total_conversions = max(float(overview["conversions"]), 1.0)
    top = model.sort_values("score_decile").iloc[0]
    capacity_row = capacity.iloc[(capacity["capacity"] - 1000).abs().argsort().iloc[0]] if not capacity.empty else None
    best_channel = str(channels.sort_values("conversion_rate", ascending=False).iloc[0]["channel_name"]) if not channels.empty else "暂无"
    best_segment = str(segments.sort_values("conversion_rate", ascending=False).iloc[0]["customer_segment"]) if not segments.empty else "暂无"
    expected_roi = float(capacity_row["expected_roi"]) if capacity_row is not None else 0.0
    return {
        "baseline_rate": round(float(overview["conversion_rate"]), 4),
        "top_decile_lift": round(float(top["lift"]), 2),
        "top_decile_capture": round(float(top["actual_conversions"]) / total_conversions, 4),
        "best_channel": best_channel,
        "best_segment": best_segment,
        "capacity": int(capacity_row["capacity"]) if capacity_row is not None else 0,
        "expected_roi": expected_roi,
        "decision_message": f"在容量 {int(capacity_row['capacity']) if capacity_row is not None else 1000:,} 的约束下，优先联系评分最高客户；前十分位 Lift 为 {float(top['lift']):.2f} 倍，建议将 {best_channel} 作为重点触达渠道。",
    }
