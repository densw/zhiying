from __future__ import annotations


def build_explanation(metrics: dict[str, object]) -> dict[str, str]:
    drift_columns = [str(item) for item in metrics.get("drift_columns", [])]
    has_drift = bool(drift_columns)
    status = "需关注" if has_drift else "稳定"
    if has_drift:
        labels = {"age": "客户年龄", "balance": "账户余额", "campaign": "联系次数", "propensity_score": "预测概率"}
        changed = "、".join(labels.get(column, column) for column in drift_columns)
        summary = f"检测到 {changed} 的分布出现变化，建议结合近期客群结构和营销节奏复核。"
    else:
        summary = "当前批次与参考样本整体稳定，未发现需要立即处理的显著分布变化。"
    return {"title": "数据质量与模型稳定性", "status": status, "summary": summary}
