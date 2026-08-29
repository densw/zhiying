from __future__ import annotations

import os

import pandas as pd
import psycopg
import streamlit as st
import plotly.express as px

from services.report_queries import REPORT_QUERIES
from services.reporting_insights import build_report_insights
from services.ui_common import apply_product_theme

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://zhiying:zhiying_local_pwd@postgres:5432/zhiying")


@st.cache_data(ttl=60)
def load_report_data() -> dict[str, pd.DataFrame]:
    with psycopg.connect(DATABASE_URL) as connection:
        return {name: pd.read_sql_query(query, connection) for name, query in REPORT_QUERIES.items()}


st.set_page_config(page_title="自动经营报告", page_icon="📝", layout="wide")
apply_product_theme("经营报告")
st.title("自动经营报告")
st.caption("从统一经营数仓自动生成的中文管理简报。")

try:
    report = load_report_data()
except Exception as error:
    st.error(f"报告数据尚未就绪，请先运行数据流水线。\n\n{error}")
    st.stop()

overview = report["overview"].iloc[0]
insights = build_report_insights(overview, report["model"], report["capacity"], report["channels"], report["segments"])
st.header("经营摘要")
kpis = st.columns(5)
kpis[0].metric("可经营客户记录", f"{int(overview['total_customers']):,}")
kpis[1].metric("成功认购", f"{int(overview['conversions']):,}")
kpis[2].metric("整体转化率", f"{float(overview['conversion_rate']):.1%}")
kpis[3].metric("平均余额", f"¥{float(overview['avg_balance']):,.0f}")
kpis[4].metric("平均联系次数", f"{float(overview['avg_campaign']):.2f}")

overview_tab, customer_tab, campaign_tab, model_tab, decision_tab, quality_tab = st.tabs(
    ["经营摘要", "客户分析", "渠道活动", "模型表现", "决策分析", "数据质量"]
)
with overview_tab:
    st.subheader("管理层结论")
    st.success(insights["decision_message"])
    conclusion_cols = st.columns(4)
    conclusion_cols[0].metric("前十分位 Lift", f"{insights['top_decile_lift']:.2f} 倍")
    conclusion_cols[1].metric("前十分位覆盖认购", f"{insights['top_decile_capture']:.1%}")
    conclusion_cols[2].metric("最优历史渠道", str(insights["best_channel"]))
    conclusion_cols[3].metric("最优客户群体", str(insights["best_segment"]))
    st.subheader("月度转化走势")
    fig = px.line(report["monthly"], x="month_label", y="conversion_rate", markers=True, labels={"month_label": "月份", "conversion_rate": "转化率"})
    fig.update_layout(height=330, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.update_xaxes(tickangle=0, automargin=True)
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("本期结论")
    st.info("高分客户集中度明显，模型优选策略在相同触达容量下能覆盖更多历史认购客户；手机渠道与高响应客群值得优先保障。")
with customer_tab:
    st.subheader("客户群体分析")
    fig = px.bar(report["segments"], x="customer_segment", y="conversion_rate", labels={"customer_segment": "客户群体", "conversion_rate": "转化率"})
    fig.update_layout(height=330, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.update_xaxes(tickangle=0, automargin=True)
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(report["segments"], use_container_width=True, hide_index=True)
with campaign_tab:
    st.subheader("渠道表现")
    st.dataframe(report["channels"], use_container_width=True, hide_index=True)
    st.subheader("活动表现")
    st.dataframe(report["campaigns"], use_container_width=True, hide_index=True)
with model_tab:
    st.subheader("评分十分位与 Lift")
    st.bar_chart(report["model"].set_index("score_decile")[["lift"]])
    st.dataframe(report["model"], use_container_width=True, hide_index=True)
with decision_tab:
    st.subheader("不同营销容量下的预期结果")
    st.dataframe(report["capacity"], use_container_width=True, hide_index=True)
with quality_tab:
    st.subheader("质量摘要")
    st.dataframe(report["quality"], use_container_width=True, hide_index=True)
    st.subheader("业务建议")
    st.dataframe(report["recommendations"], use_container_width=True, hide_index=True)
    st.subheader("专业边界与下一步")
    st.warning("这些结果描述的是历史关联，不等于因果关系。正式上线前应补充当前批次验证、随机对照实验、公平性检查、客户授权与漂移阈值治理。")
