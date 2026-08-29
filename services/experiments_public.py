from __future__ import annotations

import os

import pandas as pd
import psycopg
import streamlit as st
import plotly.express as px

from services.experiment_views import latest_candidates
from services.ui_common import apply_product_theme

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://zhiying:zhiying_local_pwd@postgres:5432/zhiying")


@st.cache_data(ttl=60)
def load_runs() -> pd.DataFrame:
    query = """
        SELECT run_id, experiment_name, model_name, feature_version,
               selected_model, training_rows, test_rows, threshold,
               roc_auc, pr_auc, precision, recall, f1, log_loss,
               brier_score, mlflow_model_uri, trained_at
        FROM ml.training_runs ORDER BY trained_at DESC
    """
    with psycopg.connect(DATABASE_URL) as connection:
        return pd.read_sql_query(query, connection)


st.set_page_config(page_title="模型实验管理", page_icon="🧪", layout="wide")
apply_product_theme("模型实验")
st.title("模型实验管理")
st.caption("中文查看每次训练运行、候选模型对比、评估指标与模型产物。")

try:
    runs = load_runs()
except Exception as error:
    st.error(f"实验记录尚未就绪，请先运行数据流水线。\n\n{error}")
    st.stop()

if runs.empty:
    st.warning("当前没有实验运行记录。")
    st.stop()

champion = runs[runs["selected_model"]].iloc[0] if runs["selected_model"].any() else runs.iloc[0]
latest = latest_candidates(runs)
metrics = st.columns(5)
metrics[0].metric("当前生产模型", str(champion["model_name"]))
metrics[1].metric("ROC-AUC", f"{float(champion['roc_auc']):.2%}")
metrics[2].metric("PR-AUC", f"{float(champion['pr_auc']):.2%}")
metrics[3].metric("召回率", f"{float(champion['recall']):.2%}")
metrics[4].metric("训练样本", f"{int(champion['training_rows']):,}")

comparison, detail, artifacts = st.tabs(["方案对比", "运行详情", "模型产物"])
with comparison:
    st.subheader("候选模型表现")
    display = latest[["model_name", "selected_model", "roc_auc", "pr_auc", "precision", "recall", "f1", "brier_score"]].copy()
    display.columns = ["模型方案", "当前生产", "ROC-AUC", "PR-AUC", "精确率", "召回率", "F1", "Brier 分数"]
    st.dataframe(display, use_container_width=True, hide_index=True)
    with st.expander("为什么看这些指标？为什么选当前生产模型？", expanded=True):
        st.markdown("**业务目标**：营销团队每天只能联系有限数量的客户，因此模型不是追求把所有人简单分成‘买/不买’，而是要把更可能认购的人排在前面。历史标签中正类占比较低，所以不能只看准确率。")
        st.markdown("**指标分工**：ROC-AUC 衡量整体排序区分能力；PR-AUC 只关注正类及其精确率，更能反映不平衡营销名单的质量，因此作为首要选型指标；召回率衡量能覆盖多少潜在认购客户；精确率衡量名单命中率；F1 用于观察二者平衡；Brier 分数衡量概率是否校准（越低越好），用于检查概率能否支持 ROI 估算。")
        st.markdown("**本次选择**：XGBoost 的 PR-AUC **46.36%**、ROC-AUC **80.32%**、F1 **44.84%** 均为三套候选方案最高，说明在相同容量下更适合把高潜客户排到前面；召回率 **67.70%** 与随机森林接近。随机森林的 Brier 分数更低（**0.1158**），概率校准更稳，因此报告中同时保留该风险提示；当前生产模型是按‘优先提升名单排序质量’的 PR-AUC 规则自动选出的，而不是宣称所有指标都最好。")
    st.subheader("核心指标对比（数值越高越好）")
    st.caption("ROC-AUC、PR-AUC、F1 分开显示，不相互累加；Brier 分数为反向指标，数值越低越好。")
    chart_cols = st.columns(3)
    for column, label, target in [("roc_auc", "ROC-AUC", 0), ("pr_auc", "PR-AUC", 1), ("f1", "F1", 2)]:
        chart_cols[target].markdown(f"**{label}**")
        chart_data = latest[["model_name", column]].copy()
        chart_data["model_name"] = chart_data["model_name"].replace({"logistic_regression": "逻辑回归", "random_forest": "随机森林", "xgboost": "XGBoost"})
        fig = px.bar(chart_data, x=column, y="model_name", orientation="h", text=column, labels={column: label, "model_name": "模型"})
        fig.update_traces(texttemplate="%{x:.2%}", textposition="outside", cliponaxis=False, marker_color="#176b87")
        fig.update_layout(height=190, margin=dict(l=8, r=28, t=4, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
        fig.update_xaxes(tickformat=".0%", range=[0, 1], automargin=True)
        fig.update_yaxes(automargin=True)
        chart_cols[target].plotly_chart(fig, use_container_width=True)
with detail:
    st.subheader("训练运行记录")
    selected_run = st.selectbox("选择一次运行", runs["run_id"].tolist())
    run = runs[runs["run_id"] == selected_run].iloc[0]
    detail_rows = pd.DataFrame({"项目": ["运行编号", "实验名称", "模型方案", "特征版本", "训练样本", "测试样本", "分类阈值", "训练时间"], "结果": [run["run_id"], run["experiment_name"], run["model_name"], run["feature_version"], f"{int(run['training_rows']):,}", f"{int(run['test_rows']):,}", f"{float(run['threshold']):.4f}", str(run["trained_at"])]})
    st.dataframe(detail_rows, use_container_width=True, hide_index=True)
with artifacts:
    st.subheader("可追溯模型产物")
    st.info("每次运行都会保存评估报告、分类报告、特征重要性与可加载模型；当前生产模型由 PR-AUC 最高的方案自动选出。")
    st.dataframe(runs[["run_id", "model_name", "mlflow_model_uri", "feature_version", "trained_at"]].rename(columns={"run_id": "运行编号", "model_name": "模型方案", "mlflow_model_uri": "模型地址", "feature_version": "特征版本", "trained_at": "训练时间"}), use_container_width=True, hide_index=True)
