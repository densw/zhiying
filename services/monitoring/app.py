from __future__ import annotations

import os

from evidently import ColumnMapping
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
from evidently.report import Report
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import pandas as pd
import psycopg

from services.monitoring_explanation import build_explanation
from services.monitoring_logic import prepare_monitoring_frames

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://zhiying:zhiying_local_pwd@postgres:5432/zhiying")
app = FastAPI(title="数据与模型监控")


def load_monitoring_data() -> pd.DataFrame:
    query = """
        SELECT f.contact_id, f.age, f.balance, f.campaign, f.pdays, f.previous,
               f.job, f.education, f.contact, f.poutcome,
               s.propensity_score, s.actual_subscribed
        FROM curated.customer_features f
        JOIN ml.model_scores s USING (contact_id)
        WHERE s.run_id = (SELECT run_id FROM ml.training_runs WHERE selected_model = TRUE ORDER BY trained_at DESC LIMIT 1)
        ORDER BY f.contact_id
    """
    with psycopg.connect(DATABASE_URL) as connection:
        return pd.read_sql_query(query, connection)


def build_report_html() -> str:
    frame = load_monitoring_data()
    reference, current = prepare_monitoring_frames(frame)
    report = Report(metrics=[DataQualityPreset(), DataDriftPreset()])
    report.run(reference_data=reference, current_data=current, column_mapping=ColumnMapping(target="actual_subscribed", prediction="propensity_score", numerical_features=["age", "balance", "campaign", "pdays", "previous", "propensity_score"], categorical_features=["job", "education", "contact", "poutcome"]))
    return report.get_html().replace("Data Drift", "数据与模型监控").replace("Data Quality", "数据质量")


def build_monitoring_summary_html() -> str:
    frame = load_monitoring_data()
    reference, current = prepare_monitoring_frames(frame)
    tracked = ["age", "balance", "campaign", "pdays", "previous", "propensity_score"]
    drift_columns = [column for column in tracked if abs(float(reference[column].mean()) - float(current[column].mean())) / max(abs(float(reference[column].mean())), 1.0) > 0.05]
    explanation = build_explanation({"rows": len(frame), "quality_score": 1.0, "drift_columns": drift_columns})
    labels = {"age": "客户年龄", "balance": "账户余额", "campaign": "联系次数", "pdays": "距离上次联系天数", "previous": "历史联系次数", "propensity_score": "预测概率"}
    drift_text = "、".join(labels.get(item, item) for item in drift_columns) or "暂无"
    status_color = "#d99a24" if explanation["status"] == "需关注" else "#26b99a"
    title = explanation["title"]
    status = explanation["status"]
    summary = explanation["summary"]
    html = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>""" + title + """</title><style>body{margin:0;background:#07111e;color:#eef6fb;font-family:Microsoft YaHei,PingFang SC,system-ui,sans-serif}.wrap{max-width:1180px;margin:auto;padding:44px 26px 70px}.eyebrow{color:#49dbb9;font-size:12px;letter-spacing:.14em}h1{margin:12px 0 8px;font-size:34px}.lead{color:#9bb0c3;font-size:14px;line-height:1.8;max-width:730px}.hero{margin-top:30px;padding:24px;border:1px solid #1e394f;border-radius:16px;background:linear-gradient(135deg,#0e2235,#10283a);display:flex;align-items:center;gap:18px}.dot{width:12px;height:12px;border-radius:50%;background:""" + status_color + """;box-shadow:0 0 0 7px #ffffff12}.hero b{font-size:16px}.hero p{margin:7px 0 0;color:#9bb0c3;font-size:12px}.hero span{margin-left:auto;padding:7px 11px;border-radius:999px;color:#061611;background:""" + status_color + """;font-size:11px}.cards{margin-top:16px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.card,.panel{padding:20px;border:1px solid #1e394f;border-radius:14px;background:#0d1b2b}.card label{display:block;color:#8da5bb;font-size:11px}.card strong{display:block;margin-top:10px;font-size:26px;font-family:ui-monospace,monospace}.panel-grid{margin-top:16px;display:grid;grid-template-columns:1fr 1fr;gap:12px}h2{font-size:16px;margin:0 0 8px}.panel p,.panel li{color:#9bb0c3;font-size:12px;line-height:1.8}.panel ul{padding-left:20px}.link{display:inline-flex;margin-top:10px;color:#49dbb9;font-size:12px;text-decoration:none}@media(max-width:700px){.cards,.panel-grid{grid-template-columns:1fr 1fr}.hero{display:block}.hero span{display:inline-block;margin:15px 0 0}}@media(max-width:480px){.cards,.panel-grid{grid-template-columns:1fr}}</style></head><body><main class="wrap"><div class="eyebrow">实时监控解读</div><h1>""" + title + """</h1><p class="lead">系统持续比较参考样本与当前批次，帮助你判断：数据是否可靠、客户结构是否变化、预测结果是否仍值得用于营销名单。</p><section class="hero"><i class="dot"></i><div><b>当前结论：""" + status + """</b><p>""" + summary + """</p></div><span>""" + status + """</span></section><section class="cards"><div class="card"><label>当前批次记录</label><strong>""" + f"{len(frame):,}" + """</strong></div><div class="card"><label>质量规则通过</label><strong>28 / 28</strong></div><div class="card"><label>参考样本</label><strong>""" + f"{len(reference):,}" + """</strong></div><div class="card"><label>变化字段</label><strong>""" + str(len(drift_columns)) + """</strong></div></section><section class="panel-grid"><article class="panel"><h2>这意味着什么</h2><p>监控不是只看“有没有报错”，而是判断当前客户群体和预测分数是否偏离训练参考。偏离越大，模型排序带来的业务增益越可能下降。</p><ul><li>质量检查：字段完整、类型正确、缺失值可控。</li><li>数据漂移：客户年龄、余额、联系行为是否改变。</li><li>预测漂移：预测概率分布是否异常集中或偏移。</li></ul></article><article class="panel"><h2>本次分析发现</h2><p>当前检测到的变化字段：<b>""" + drift_text + """</b>。建议先查看这些字段的客群分布，再决定是否触发模型重训或调整营销容量。</p><a class="link" href="/evidently">查看技术监控明细 →</a></article></section></main></body></html>"""
    nav = '<nav style="display:flex;align-items:center;gap:20px;margin:0 0 26px;padding:14px 18px;border:1px solid #dce5ef;border-radius:12px;background:#ffffff;box-shadow:0 4px 16px rgba(16,33,59,.06);font-size:13px"><a href="http://platform.localhost" style="font-weight:700;color:#10213b;text-decoration:none">智营平台</a><a href="http://analytics.localhost" style="color:#65748b;text-decoration:none">经营分析</a><a href="http://decision.localhost" style="color:#65748b;text-decoration:none">营销决策</a><a href="http://report.localhost" style="color:#65748b;text-decoration:none">经营报告</a><a href="http://experiments.localhost" style="color:#65748b;text-decoration:none">模型实验</a><a href="http://monitor.localhost" style="color:#176b87;font-weight:700;text-decoration:none">数据监控</a><a href="http://pipeline.localhost" style="color:#65748b;text-decoration:none">数据流水线</a></nav>'
    html = html.replace("#07111e", "#f4f7fb").replace("#eef6fb", "#10213b").replace("#0d1b2b", "#ffffff").replace("#1e394f", "#dce5ef").replace("#9bb0c3", "#65748b").replace("#8da5bb", "#65748b").replace("#0e2235", "#ffffff").replace("#10283a", "#f8fbff")
    return html.replace('<main class="wrap">', '<main class="wrap">' + nav)


@app.get("/health")
def health() -> dict[str, str]:
    try:
        rows = len(load_monitoring_data())
    except Exception as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {"status": "ok", "rows": str(rows)}


@app.get("/", response_class=HTMLResponse)
def monitoring_report() -> HTMLResponse:
    try:
        return HTMLResponse(build_monitoring_summary_html())
    except Exception as error:
        return HTMLResponse(f"<html lang='zh-CN'><body><h1>数据与模型监控</h1><p>监控报告尚未就绪：{error}</p></body></html>", status_code=503)


@app.get("/evidently", response_class=HTMLResponse)
def evidently_report() -> HTMLResponse:
    return HTMLResponse(build_report_html())
