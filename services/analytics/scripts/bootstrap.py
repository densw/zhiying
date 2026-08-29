from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg2
import requests


ROOT = Path("/workspace")
SQL_PATH = ROOT / "sql" / "analytics_views.sql"


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
      raise RuntimeError(f"missing env: {name}")
    return value


DB_CONFIG = {
    "dbname": env("POSTGRES_DB"),
    "user": env("POSTGRES_USER"),
    "password": env("POSTGRES_PASSWORD"),
    "host": env("POSTGRES_HOST"),
    "port": env("POSTGRES_PORT"),
}


SUPERSET_BASE_URL = env("SUPERSET_BASE_URL")
SUPERSET_USERNAME = env("SUPERSET_USERNAME")
SUPERSET_PASSWORD = env("SUPERSET_PASSWORD")


def wait_for_postgres() -> None:
    for _ in range(60):
        try:
            with psycopg2.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("select 1")
                    cursor.fetchone()
            return
        except psycopg2.OperationalError:
            time.sleep(2)
    raise RuntimeError("postgres not ready")


def wait_for_superset() -> None:
    for _ in range(90):
        try:
            response = requests.get(f"{SUPERSET_BASE_URL}/health", timeout=10)
            if response.ok:
                return
        except requests.RequestException:
            pass
        time.sleep(2)
    raise RuntimeError("superset not ready")


def seed_database() -> None:
    ddl = SQL_PATH.read_text(encoding="utf-8")
    with psycopg2.connect(**DB_CONFIG) as conn:
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(ddl)


class SupersetClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login = self.session.post(
            f"{SUPERSET_BASE_URL}/api/v1/security/login",
            json={
                "username": SUPERSET_USERNAME,
                "password": SUPERSET_PASSWORD,
                "provider": "db",
                "refresh": True,
            },
            timeout=20,
        )
        login.raise_for_status()
        access_token = login.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {access_token}"})

    def list_items(self, path: str) -> list[dict[str, Any]]:
        response = self.session.get(f"{SUPERSET_BASE_URL}{path}", timeout=30)
        response.raise_for_status()
        payload = response.json()
        return payload.get("result", payload)

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.session.post(
            f"{SUPERSET_BASE_URL}{path}",
            data=json.dumps(payload),
            timeout=30,
        )
        if not response.ok:
            raise RuntimeError(f"Superset API {path} failed {response.status_code}: {response.text}")
        return response.json()

    def put(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.session.put(
            f"{SUPERSET_BASE_URL}{path}",
            data=json.dumps(payload),
            timeout=30,
        )
        if not response.ok:
            raise RuntimeError(f"Superset API {path} failed {response.status_code}: {response.text}")
        return response.json()


def by_name(items: list[dict[str, Any]], key: str, expected: str) -> dict[str, Any] | None:
    for item in items:
        if item.get(key) == expected:
            return item
    return None


def upsert_database(client: SupersetClient) -> int:
    name = "经营分析数仓"
    existing = by_name(client.list_items("/api/v1/database/?q=(page:0,page_size:100)"), "database_name", name)
    payload = {
        "database_name": name,
        "engine": "postgresql",
        "configuration_method": "sqlalchemy_form",
        "sqlalchemy_uri": (
            f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
        ),
        "expose_in_sqllab": True,
        "allow_ctas": False,
        "allow_cvas": False,
        "allow_run_async": False,
    }
    if existing:
        client.put(f"/api/v1/database/{existing['id']}", payload)
        return int(existing["id"])
    created = client.post("/api/v1/database/", payload)
    return int(created["id"])


def upsert_dataset(client: SupersetClient, database_id: int, schema: str, table_name: str) -> int:
    full_name = f"{schema}.{table_name}"
    datasets = client.list_items("/api/v1/dataset/?q=(page:0,page_size:200)")
    existing = None
    for item in datasets:
        if item.get("table_name") == table_name and item.get("schema") == schema:
            existing = item
            break
    payload = {
        "database_id": database_id,
        "schema": schema,
        "table_name": table_name,
        "owners": [],
    }
    if existing:
        client.put(f"/api/v1/dataset/{existing['id']}", payload)
        return int(existing["id"])
    created = client.post("/api/v1/dataset/", payload)
    return int(created["id"])


def table_form_data(dataset_id: int, columns: list[str], order_by: str | None = None) -> dict[str, Any]:
    sort_by: list[list[Any]] = []
    if order_by:
        sort_by = [[order_by, True]]
    return {
        "datasource": f"{dataset_id}__table",
        "viz_type": "table",
        "all_columns": columns,
        "adhoc_filters": [],
        "row_limit": 100,
        "order_desc": True,
        "server_pagination": False,
        "sort_by": sort_by,
    }


def bar_form_data(dataset_id: int, x_axis: str, metric: str, groupby: list[str] | None = None) -> dict[str, Any]:
    return {
        "datasource": f"{dataset_id}__table",
        "viz_type": "echarts_bar",
        "adhoc_filters": [],
        "metrics": [metric],
        "groupby": groupby or [],
        "x_axis": x_axis,
        "row_limit": 100,
        "contributionMode": None,
        "seriesType": "bar",
        "stack": False,
        "show_legend": True,
        "truncateXAxis": False,
        "rich_tooltip": True,
    }


def line_form_data(dataset_id: int, x_axis: str, metric: str) -> dict[str, Any]:
    return {
        "datasource": f"{dataset_id}__table",
        "viz_type": "echarts_timeseries_line",
        "adhoc_filters": [],
        "metrics": [metric],
        "x_axis": x_axis,
        "time_grain_sqla": None,
        "row_limit": 100,
        "show_legend": True,
        "rich_tooltip": True,
    }


def big_number_form_data(dataset_id: int, metric: str) -> dict[str, Any]:
    return {
        "datasource": f"{dataset_id}__table",
        "viz_type": "big_number_total",
        "adhoc_filters": [],
        "metric": metric,
        "subheader": "",
    }


@dataclass
class ChartSpec:
    name: str
    dataset_key: str
    viz_type: str
    form_data: dict[str, Any]


@dataclass
class DashboardSpec:
    title: str
    chart_names: list[str]


def upsert_chart(client: SupersetClient, datasets: dict[str, int], spec: ChartSpec) -> int:
    charts = client.list_items("/api/v1/chart/?q=(page:0,page_size:200)")
    existing = by_name(charts, "slice_name", spec.name)
    payload = {
      "slice_name": spec.name,
      "datasource_id": datasets[spec.dataset_key],
      "datasource_type": "table",
      "viz_type": spec.viz_type,
      "params": json.dumps(spec.form_data, ensure_ascii=False),
    }
    if existing:
        client.put(f"/api/v1/chart/{existing['id']}", payload)
        return int(existing["id"])
    created = client.post("/api/v1/chart/", payload)
    return int(created["id"])


def build_position_json(chart_ids: list[int]) -> str:
    positions: dict[str, Any] = {
        "ROOT_ID": {
            "children": ["GRID_ID"],
            "id": "ROOT_ID",
            "meta": {"text": "ROOT"},
            "type": "ROOT",
        },
        "GRID_ID": {
            "children": [],
            "id": "GRID_ID",
            "parents": ["ROOT_ID"],
            "type": "GRID",
        },
    }
    current_y = 0
    for index, chart_id in enumerate(chart_ids):
        row_id = f"ROW-{index + 1}"
        chart_node = f"CHART-{chart_id}"
        positions["GRID_ID"]["children"].append(row_id)
        positions[row_id] = {
            "children": [chart_node],
            "id": row_id,
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        }
        positions[chart_node] = {
            "children": [],
            "id": chart_node,
            "meta": {
                "chartId": chart_id,
                "height": 50,
                "sliceName": chart_node,
                "uuid": chart_node,
                "width": 12,
            },
            "parents": ["ROOT_ID", "GRID_ID", row_id],
            "type": "CHART",
        }
        current_y += 1
    return json.dumps(positions, ensure_ascii=False)


def upsert_dashboard(client: SupersetClient, chart_name_to_id: dict[str, int], spec: DashboardSpec) -> None:
    dashboards = client.list_items("/api/v1/dashboard/?q=(page:0,page_size:100)")
    existing = by_name(dashboards, "dashboard_title", spec.title)
    chart_ids = [chart_name_to_id[name] for name in spec.chart_names]
    payload = {
        "dashboard_title": spec.title,
        "slug": spec.title.replace(" ", "-")[:80],
        "position_json": build_position_json(chart_ids),
        "published": True,
        "css": "",
        "json_metadata": json.dumps(
            {
                "timed_refresh_immune_slices": [],
                "expanded_slices": {},
                "color_scheme": "",
            },
            ensure_ascii=False,
        ),
        "owners": [],
    }
    if existing:
        client.put(f"/api/v1/dashboard/{existing['id']}", payload)
    else:
        client.post("/api/v1/dashboard/", payload)


def bootstrap_superset() -> None:
    client = SupersetClient()
    database_id = upsert_database(client)
    dataset_map = {
        "executive_overview": ("analytics", "executive_overview"),
        "monthly_conversion": ("analytics", "monthly_conversion"),
        "customer_profile": ("analytics", "customer_profile"),
        "customer_segment_performance": ("analytics", "customer_segment_performance"),
        "channel_performance": ("analytics", "channel_performance"),
        "campaign_performance": ("analytics", "campaign_performance"),
        "model_quality_overview": ("analytics", "model_quality_overview"),
        "capacity_scenarios": ("analytics", "capacity_scenarios"),
        "recommendations": ("analytics", "recommendations"),
    }
    dataset_ids = {
        key: upsert_dataset(client, database_id, schema, table)
        for key, (schema, table) in dataset_map.items()
    }

    chart_specs = [
        ChartSpec(
            name="总客户数",
            dataset_key="executive_overview",
            viz_type="big_number_total",
            form_data=big_number_form_data(dataset_ids["executive_overview"], "total_customers"),
        ),
        ChartSpec(
            name="总体转化率",
            dataset_key="executive_overview",
            viz_type="big_number_total",
            form_data=big_number_form_data(dataset_ids["executive_overview"], "conversion_rate"),
        ),
        ChartSpec(
            name="月度转化走势",
            dataset_key="monthly_conversion",
            viz_type="echarts_timeseries_line",
            form_data=line_form_data(dataset_ids["monthly_conversion"], "month_label", "conversion_rate"),
        ),
        ChartSpec(
            name="客群表现分布",
            dataset_key="customer_segment_performance",
            viz_type="echarts_bar",
            form_data=bar_form_data(dataset_ids["customer_segment_performance"], "customer_segment", "conversion_rate"),
        ),
        ChartSpec(
            name="客户结构明细",
            dataset_key="customer_profile",
            viz_type="table",
            form_data=table_form_data(dataset_ids["customer_profile"], ["customer_segment", "age_band", "job", "education", "balance_band", "converted"]),
        ),
        ChartSpec(
            name="渠道效率对比",
            dataset_key="channel_performance",
            viz_type="echarts_bar",
            form_data=bar_form_data(dataset_ids["channel_performance"], "channel_name", "conversion_rate"),
        ),
        ChartSpec(
            name="渠道经营概览",
            dataset_key="channel_performance",
            viz_type="table",
            form_data=table_form_data(dataset_ids["channel_performance"], ["channel_name", "contacts", "conversions", "conversion_rate", "avg_attempts", "avg_balance"]),
        ),
        ChartSpec(
            name="活动批次表现",
            dataset_key="campaign_performance",
            viz_type="echarts_bar",
            form_data=bar_form_data(dataset_ids["campaign_performance"], "campaign_band", "conversion_rate", ["previous_outcome"]),
        ),
        ChartSpec(
            name="活动效果明细",
            dataset_key="campaign_performance",
            viz_type="table",
            form_data=table_form_data(dataset_ids["campaign_performance"], ["campaign_band", "previous_outcome", "contacts", "conversions", "conversion_rate", "avg_balance"]),
        ),
        ChartSpec(
            name="分位增益",
            dataset_key="model_quality_overview",
            viz_type="echarts_bar",
            form_data=bar_form_data(dataset_ids["model_quality_overview"], "score_decile", "lift"),
        ),
        ChartSpec(
            name="分位质量明细",
            dataset_key="model_quality_overview",
            viz_type="table",
            form_data=table_form_data(dataset_ids["model_quality_overview"], ["score_decile", "customer_count", "avg_probability", "actual_rate", "lift"]),
        ),
        ChartSpec(
            name="容量策略模拟",
            dataset_key="capacity_scenarios",
            viz_type="table",
            form_data=table_form_data(dataset_ids["capacity_scenarios"], ["capacity", "selected_customers", "expected_conversions", "avg_probability", "precision", "lift", "expected_roi"]),
        ),
    ]
    chart_ids = {spec.name: upsert_chart(client, dataset_ids, spec) for spec in chart_specs}

    dashboard_specs = [
        DashboardSpec("经营总览看板", ["总客户数", "总体转化率", "月度转化走势"]),
        DashboardSpec("客户分析看板", ["客群表现分布", "客户结构明细"]),
        DashboardSpec("渠道分析看板", ["渠道效率对比", "渠道经营概览"]),
        DashboardSpec("活动分析看板", ["活动批次表现", "活动效果明细"]),
        DashboardSpec("模型运营看板", ["分位增益", "分位质量明细", "容量策略模拟"]),
    ]
    for spec in dashboard_specs:
        upsert_dashboard(client, chart_ids, spec)


def main() -> None:
    wait_for_postgres()
    seed_database()
    wait_for_superset()
    bootstrap_superset()
    print("analytics bootstrap completed")


if __name__ == "__main__":
    main()
