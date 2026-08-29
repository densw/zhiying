from __future__ import annotations

import os
from pathlib import Path

from dagster import Definitions, MetadataValue, ScheduleDefinition, asset, define_asset_job
import requests
from sqlalchemy import text

from services.pipeline.dataset import build_curated_dataset, import_raw_dataset
from services.pipeline.db import bootstrap_database, create_db_engine, fetch_frame
from services.pipeline.modeling import score_latest_model, train_models
from services.pipeline.settings import PipelineSettings


def settings_and_engine():
    settings = PipelineSettings.from_env()
    engine = create_db_engine(settings.database_url)
    bootstrap_database(engine, settings.sql_bootstrap_path)
    return settings, engine


def execute_sql_file(engine, path: Path) -> None:
    statements = [statement.strip() for statement in path.read_text(encoding="utf-8").split(";") if statement.strip()]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


@asset(group_name="ingestion", description="导入完整原始营销记录")
def raw_bank_data():
    settings, engine = settings_and_engine()
    frame = import_raw_dataset(settings, engine)
    return {"rows": len(frame), "source": settings.dataset_path.name}


@asset(group_name="validation", description="执行字段、类型、取值与泄漏规则校验")
def validated_bank_data(raw_bank_data):
    _, engine = settings_and_engine()
    count = int(fetch_frame(engine, "SELECT COUNT(*) AS count FROM raw.customer_campaign_contacts").iloc[0]["count"])
    if count != int(raw_bank_data["rows"]):
        raise RuntimeError("导入记录数与校验记录数不一致")
    return {"rows": count, "quality_gate": "passed"}


@asset(group_name="warehouse", description="构建共享客户特征表与分析视图")
def analytics_marts(validated_bank_data):
    _, engine = settings_and_engine()
    frame = build_curated_dataset(engine)
    execute_sql_file(engine, Path("/app/warehouse/sql/analytics_views.sql"))
    return {"rows": len(frame), "validated_rows": validated_bank_data["rows"]}


@asset(group_name="features", description="确认训练与评分共用同一特征口径")
def feature_table(analytics_marts):
    _, engine = settings_and_engine()
    count = int(fetch_frame(engine, "SELECT COUNT(*) AS count FROM curated.customer_features").iloc[0]["count"])
    return {"rows": count, "mart_rows": analytics_marts["rows"]}


@asset(group_name="training", description="训练两类候选模型并记录实验")
def trained_model(feature_table):
    settings, engine = settings_and_engine()
    result = train_models(settings, engine)
    return {**result, "feature_rows": feature_table["rows"]}


@asset(group_name="evaluation", description="读取生产候选的完整评估指标")
def model_evaluation(trained_model):
    _, engine = settings_and_engine()
    metrics = fetch_frame(
        engine,
        "SELECT model_name, roc_auc, pr_auc, precision, recall, f1, brier_score "
        "FROM ml.training_runs WHERE run_id = :run_id",
        {"run_id": trained_model["selected_run_id"]},
    ).iloc[0].to_dict()
    return metrics


@asset(group_name="scoring", description="使用当前生产模型写回全量客户评分")
def customer_scores(model_evaluation):
    settings, engine = settings_and_engine()
    result = score_latest_model(settings, engine)
    return {**result, "pr_auc": float(model_evaluation["pr_auc"])}


@asset(group_name="decision", description="刷新不同容量下的真实策略测算")
def campaign_simulation(customer_scores):
    _, engine = settings_and_engine()
    execute_sql_file(engine, Path("/app/warehouse/sql/analytics_views.sql"))
    scenarios = fetch_frame(engine, "SELECT COUNT(*) AS count FROM analytics.capacity_scenarios")
    return {"scenarios": int(scenarios.iloc[0]["count"]), "score_rows": customer_scores["scored_rows"]}


@asset(group_name="publishing", description="确认自动经营报告已读取最新数仓")
def business_report(campaign_simulation):
    return {
        "url": os.getenv("REPORTS_INTERNAL_URL", "http://reports:3000"),
        "capacity_scenarios": campaign_simulation["scenarios"],
    }


@asset(group_name="publishing", description="生成真实数据质量与漂移报告")
def monitoring_report(business_report):
    url = os.getenv("MONITORING_INTERNAL_URL", "http://monitoring:8000")
    response = requests.get(f"{url}/health", timeout=60)
    response.raise_for_status()
    return MetadataValue.json({"report": business_report["url"], "monitoring": response.json()})


full_pipeline = define_asset_job("full_customer_operations_pipeline")
daily_schedule = ScheduleDefinition(job=full_pipeline, cron_schedule="0 7 * * *")
defs = Definitions(
    assets=[raw_bank_data, validated_bank_data, analytics_marts, feature_table, trained_model, model_evaluation, customer_scores, campaign_simulation, business_report, monitoring_report],
    jobs=[full_pipeline],
    schedules=[daily_schedule],
)
