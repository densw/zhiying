from __future__ import annotations

import os

import pandas as pd
import psycopg
import streamlit as st
import plotly.express as px

from services.analytics_queries import ANALYTICS_QUERIES
from services.ui_common import apply_product_theme

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://zhiying:zhiying_local_pwd@postgres:5432/zhiying")


@st.cache_data(ttl=60)
def load_marts() -> dict[str, pd.DataFrame]:
    with psycopg.connect(DATABASE_URL) as connection:
        return {name: pd.read_sql_query(query, connection) for name, query in ANALYTICS_QUERIES.items()}


st.set_page_config(page_title="经营分析中心", page_icon="📊", layout="wide")
apply_product_theme("经营分析")
st.title("经营分析中心")
st.caption("基于统一经营数仓的客户、渠道、活动与模型运营分析。")

try:
    marts = load_marts()
except Exception as error:
    st.error(f"分析数据尚未就绪，请先运行数据流水线。\n\n{error}")
    st.stop()

overview = marts["overview"].iloc[0]
metrics = st.columns(5)
metrics[0].metric("可经营客户记录", f"{int(overview['total_customers']):,}")
metrics[1].metric("成功认购", f"{int(overview['conversions']):,}")
metrics[2].metric("整体转化率", f"{float(overview['conversion_rate']):.1%}")
metrics[3].metric("平均账户余额", f"¥{float(overview['avg_balance']):,.0f}")
metrics[4].metric("平均联系次数", f"{float(overview['avg_campaign']):.2f}")

overview_tab, customer_tab, campaign_tab, model_tab = st.tabs(["经营总览", "客户分析", "渠道与活动", "模型运营"])
with overview_tab:
    left, right = st.columns(2)
    with left:
        st.subheader("月度转化走势")
        fig = px.line(marts["monthly"], x="month_label", y="conversion_rate", markers=True, labels={"month_label": "月份", "conversion_rate": "转化率"})
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(tickangle=0, automargin=True)
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("客户群体表现")
        fig = px.bar(marts["segments"], x="customer_segment", y="conversion_rate", labels={"customer_segment": "客户群体", "conversion_rate": "转化率"})
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(tickangle=0, automargin=True)
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("重点经营发现")
    st.info("评分最高的客户分位覆盖了更多历史认购客户；手机渠道整体转化高于未识别渠道；联系次数过高时转化出现边际递减。")
with customer_tab:
    st.subheader("客户群体明细")
    st.dataframe(marts["segments"], use_container_width=True, hide_index=True)
with campaign_tab:
    left, right = st.columns(2)
    with left:
        st.subheader("渠道表现")
        st.dataframe(marts["channels"], use_container_width=True, hide_index=True)
    with right:
        st.subheader("活动批次表现")
        st.dataframe(marts["campaigns"], use_container_width=True, hide_index=True)
with model_tab:
    st.subheader("评分十分位运营表现")
    st.bar_chart(marts["model"].set_index("score_decile")[["lift"]])
    st.dataframe(marts["model"], use_container_width=True, hide_index=True)
