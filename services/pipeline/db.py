from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def create_db_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True, future=True)


def bootstrap_database(engine: Engine, sql_path: Path) -> None:
    script = sql_path.read_text(encoding="utf-8")
    with engine.begin() as connection:
        for statement in [part.strip() for part in script.split(";") if part.strip()]:
            connection.execute(text(statement))


def parse_table_ref(table_ref: str) -> tuple[str | None, str]:
    parts = table_ref.split(".", maxsplit=1)
    if len(parts) == 1:
        return None, parts[0]
    return parts[0], parts[1]


def fetch_frame(engine: Engine, query: str, params: dict | None = None) -> pd.DataFrame:
    with engine.connect() as connection:
        return pd.read_sql(text(query), connection, params=params or {})


def replace_table_contents(engine: Engine, table_ref: str, frame: pd.DataFrame) -> None:
    schema, table = parse_table_ref(table_ref)
    with engine.begin() as connection:
        if schema:
            connection.execute(
                text(f'TRUNCATE TABLE "{schema}"."{table}" RESTART IDENTITY CASCADE')
            )
        else:
            connection.execute(text(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE'))
        frame.to_sql(
            table,
            connection,
            schema=schema,
            if_exists="append",
            index=False,
            chunksize=2000,
            method="multi",
        )


def append_table_contents(engine: Engine, table_ref: str, frame: pd.DataFrame) -> None:
    schema, table = parse_table_ref(table_ref)
    with engine.begin() as connection:
        frame.to_sql(
            table,
            connection,
            schema=schema,
            if_exists="append",
            index=False,
            chunksize=2000,
            method="multi",
        )


def delete_run_outputs(engine: Engine, run_id: str) -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM ml.model_scores WHERE run_id = :run_id"), {"run_id": run_id})
        connection.execute(
            text("DELETE FROM ml.model_score_deciles WHERE run_id = :run_id"),
            {"run_id": run_id},
        )


def clear_selected_models(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("UPDATE ml.training_runs SET selected_model = FALSE WHERE selected_model = TRUE"))
