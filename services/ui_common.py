from __future__ import annotations

import streamlit as st

NAV_ITEMS = [("平台首页", "http://platform.localhost"), ("经营分析", "http://analytics.localhost"), ("营销决策", "http://decision.localhost"), ("经营报告", "http://report.localhost"), ("模型实验", "http://experiments.localhost"), ("数据监控", "http://monitor.localhost"), ("数据流水线", "http://pipeline.localhost")]


def apply_product_theme(active: str) -> None:
    st.markdown("""<style>
    .stApp { background:#f4f7fb; color:#10213b; }
    [data-testid="stHeader"] { background:rgba(244,247,251,.96); }
    .block-container { max-width:1400px; padding-top:1.1rem; }
    .product-nav { position:relative; z-index:10; display:flex; align-items:center; gap:2px; padding:8px 0 13px; border-bottom:1px solid #dce5ef; margin:34px 0 24px; overflow-x:auto; scrollbar-width:none; background:#f4f7fb; }
    .product-nav::-webkit-scrollbar { display:none; }
    .product-nav .nav-brand { display:flex; align-items:center; gap:8px; margin-right:18px; color:#10213b; font-weight:750; font-size:14px; white-space:nowrap; flex:0 0 auto; }
    .product-nav .nav-brand i { width:26px; height:26px; display:grid; place-items:center; border-radius:8px; color:#fff; background:#176b87; font-style:normal; }
    .product-nav a { position:relative; color:#65748b; text-decoration:none; font-size:11px; white-space:nowrap; padding:8px 9px; border-radius:6px; flex:0 0 auto; }
    .product-nav a:hover { color:#176b87; background:#e8f0f5; }
    .product-nav a.active { color:#176b87; font-weight:700; background:transparent; box-shadow:inset 0 -2px #176b87; }
    .product-nav a.active::after { display:none; }
    h1,h2,h3 { letter-spacing:-.035em; color:#10213b; }
    [data-testid="stMetric"] { background:#ffffff; border:1px solid #dce5ef; border-radius:12px; padding:14px; }
    [data-testid="stMetricLabel"] { color:#65748b; }
    [data-testid="stMetricValue"] { color:#10213b; }
    [data-testid="stTabs"] button { color:#65748b; }
    [data-testid="stTabs"] button[aria-selected="true"] { color:#176b87; }
    [data-testid="stMarkdownContainer"] p, [data-testid="stCaptionContainer"] { color:#65748b; }
    </style>""", unsafe_allow_html=True)
    links = "".join(f'<a class="{"active" if label == active else ""}" href="{url}">{label}</a>' for label, url in NAV_ITEMS)
    st.markdown(f'<nav class="product-nav"><a class="nav-brand" href="http://platform.localhost"><i>智</i>智营平台</a>{links}</nav>', unsafe_allow_html=True)
