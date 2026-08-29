from __future__ import annotations

import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import psycopg
import streamlit as st
import plotly.express as px

from services.decision_engine import REQUIRED_NATIVE_COLUMNS, align_training_features, rank_new_batch
from services.ui_common import apply_product_theme

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://zhiying:zhiying_local_pwd@postgres:5432/zhiying")
RUNTIME_DIR = Path(os.getenv("PIPELINE_RUNTIME_DIR", "/app/runtime"))


@st.cache_data(ttl=60)
def load_reference_rows() -> pd.DataFrame:
    with psycopg.connect(DATABASE_URL) as connection:
        return pd.read_sql_query(
            "SELECT age, job, marital, education, \"default\", balance, housing, loan, contact, day, month, campaign, pdays, previous, poutcome FROM curated.customer_features",
            connection,
        )


@st.cache_resource
def load_champion_model():
    manifest_path = RUNTIME_DIR / "models" / "latest_model.json"
    if not manifest_path.exists():
        raise FileNotFoundError("尚未找到训练好的生产模型，请先运行数据流水线。")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    model_path = RUNTIME_DIR.parent / manifest["model_relative_path"] if not manifest["model_relative_path"].startswith("/app/runtime") else Path(manifest["model_relative_path"])
    if not model_path.exists():
        model_path = RUNTIME_DIR / "models" / Path(manifest["model_relative_path"]).name
    return joblib.load(model_path), manifest


def simulate_new_batch(reference: pd.DataFrame, size: int, seed: int) -> pd.DataFrame:
    sampled = reference.sample(n=size, replace=True, random_state=seed).reset_index(drop=True)
    rng = np.random.default_rng(seed)
    sampled["age"] = np.clip(sampled["age"] + rng.integers(-3, 4, size=size), 18, 95)
    sampled["balance"] = (sampled["balance"] + rng.normal(0, 250, size=size)).round().astype(int)
    sampled["campaign"] = np.clip(sampled["campaign"] + rng.choice([-1, 0, 0, 1], size=size), 1, 20)
    sampled.insert(0, "customer_code", [f"NEW-{seed:02d}-{index:05d}" for index in range(1, size + 1)])
    return sampled


st.set_page_config(page_title="营销决策中心", page_icon="🎯", layout="wide")
apply_product_theme("营销决策")
st.title("营销决策中心")
st.caption("上传或模拟一批新客户，使用已训练模型生成触达优先级。")

try:
    model, manifest = load_champion_model()
    reference = load_reference_rows()
except Exception as error:
    st.error(str(error))
    st.stop()

st.info("完整流程：新客户数据 → 字段对齐 → 概率预测 → 优先级排序 → 按营销容量生成名单。通话时长等通话后字段不会进入模型。")
with st.expander("数据来源与字段说明（面试讲解）", expanded=False):
    st.markdown("**数据来源**：本地保存的公开银行营销历史记录（45,211 条客户联系样本），已导入平台数仓并完成质量校验。每行代表一次客户营销联系，标签是本次活动后是否认购定期存款。页面上传的新批次沿用同一套客户画像字段，便于真实演示从数据到名单的完整流程。")
    field_rows = [
        ("age", "客户年龄", "训练特征"), ("job", "职业类别", "训练特征"), ("marital", "婚姻状态", "训练特征"),
        ("education", "教育程度", "训练特征"), ("default", "是否有违约记录", "训练特征"), ("balance", "账户余额", "训练特征"),
        ("housing", "是否有住房贷款", "训练特征"), ("loan", "是否有个人贷款", "训练特征"), ("contact", "联系渠道", "训练特征"),
        ("day", "本月联系日", "训练特征"), ("month", "本次联系月份", "映射为 month_number"), ("campaign", "本次活动联系次数", "训练特征"),
        ("pdays", "距离上次联系天数", "训练特征"), ("previous", "历史联系次数", "训练特征"), ("poutcome", "上次活动结果", "训练特征"),
        ("y", "是否认购标签", "仅历史训练"), ("duration", "通话时长", "禁止用于预测（通话后才知道）"),
    ]
    st.dataframe(pd.DataFrame(field_rows, columns=["原始字段", "中文含义", "使用方式"]), hide_index=True, use_container_width=True)
upload = st.file_uploader("上传新客户 CSV（使用原始字段口径，不需要 y 和 duration）", type=["csv"])
left, right = st.columns(2)
with left:
    batch_size = st.slider("模拟新客户数量", 100, 5000, 1000, 100)
    seed = st.number_input("模拟批次编号", min_value=1, value=7, step=1)
with right:
    capacity = st.slider("计划触达容量", 50, batch_size, min(500, batch_size), 50)
    contact_cost = st.number_input("单次触达成本", min_value=0.1, value=18.0, step=1.0)
    customer_value = st.number_input("单客预期价值", min_value=1.0, value=680.0, step=10.0)

if upload is not None:
    try:
        new_batch = pd.read_csv(upload)
        source_label = f"上传批次 · {len(new_batch):,} 条"
    except Exception as error:
        st.error(f"CSV 读取失败：{error}")
        st.stop()
else:
    new_batch = simulate_new_batch(reference, batch_size, int(seed))
    source_label = f"模拟批次 · {len(new_batch):,} 条"

st.subheader(f"{source_label} · 原始字段预览")
st.dataframe(new_batch.head(8), use_container_width=True, hide_index=True)

try:
    aligned = align_training_features(new_batch)
    probabilities = model.predict_proba(aligned)[:, 1]
except Exception as error:
    st.error(f"字段对齐或模型预测失败：{error}")
    st.stop()

scored = new_batch.copy()
scored["propensity_score"] = probabilities
ranked = rank_new_batch(scored)
selected = ranked.head(min(capacity, len(ranked))).copy()
expected_conversions = float(selected["propensity_score"].sum())
expected_cost = len(selected) * contact_cost
expected_revenue = expected_conversions * customer_value
roi = (expected_revenue - expected_cost) / expected_cost if expected_cost else 0.0

st.success(f"已使用生产模型 {manifest['model_name']} 完成 {len(ranked):,} 条新客户预测。")
metrics = st.columns(5)
metrics[0].metric("新客户数", f"{len(ranked):,}")
metrics[1].metric("入选名单", f"{len(selected):,}")
metrics[2].metric("预计转化", f"{expected_conversions:,.1f}")
metrics[3].metric("名单平均概率", f"{selected['propensity_score'].mean():.1%}")
metrics[4].metric("预计 ROI", f"{roi:.1%}")

st.subheader("预测概率分布")
bins = np.linspace(0, 1, 11)
labels = [f"{left:.1f}–{right:.1f}" for left, right in zip(bins[:-1], bins[1:])]
distribution = pd.cut(ranked["propensity_score"].clip(0, 1), bins=bins, labels=labels, include_lowest=True).value_counts(sort=False).rename_axis("概率区间").reset_index(name="客户数")
fig = px.bar(distribution, x="概率区间", y="客户数", text="客户数", labels={"概率区间": "预测认购概率区间", "客户数": "客户数"})
fig.update_traces(marker_color="#176b87", textposition="outside")
fig.update_layout(height=360, margin=dict(l=20, r=20, t=30, b=20), xaxis=dict(tickangle=0, type="category", categoryorder="array", categoryarray=labels), yaxis=dict(rangemode="tozero"), showlegend=False)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
st.subheader("推荐触达名单（Top-N）")
display = selected.rename(columns={"customer_code": "客户编号", "propensity_score": "认购概率", "score_decile": "评分十分位", "priority_tier": "优先级", "recommended_channel": "推荐渠道", "priority_rank": "优先顺序"})
display["认购概率"] = display["认购概率"].map(lambda value: f"{value:.2%}")
st.dataframe(display[["客户编号", "认购概率", "评分十分位", "优先级", "推荐渠道", "优先顺序"]], use_container_width=True, hide_index=True)
st.download_button("下载本批次优先名单", display.to_csv(index=False).encode("utf-8-sig"), file_name=f"新客户优先名单-{len(selected)}.csv", mime="text/csv")
