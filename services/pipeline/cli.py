from __future__ import annotations

import argparse
import json

from services.pipeline.dataset import build_curated_dataset, import_raw_dataset
from services.pipeline.db import bootstrap_database, create_db_engine
from services.pipeline.db import fetch_frame
from services.pipeline.modeling import score_latest_model, train_models
from services.pipeline.settings import PipelineSettings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Customer propensity pipeline CLI")
    parser.add_argument("--dataset-path")
    parser.add_argument("--database-url")
    parser.add_argument("--tracking-uri")
    parser.add_argument("--experiment-name")

    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("init-db", "load-data", "build-features", "train", "score", "run-all", "ensure-ready"):
        subparsers.add_parser(command)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = PipelineSettings.from_env().override(
        dataset_path=args.dataset_path,
        database_url=args.database_url,
        mlflow_tracking_uri=args.tracking_uri,
        mlflow_experiment_name=args.experiment_name,
    )
    engine = create_db_engine(settings.database_url)

    if args.command == "init-db":
        bootstrap_database(engine, settings.sql_bootstrap_path)
        print(json.dumps({"status": "ok", "database": settings.database_url}, ensure_ascii=False))
        return

    bootstrap_database(engine, settings.sql_bootstrap_path)

    if args.command == "load-data":
        staged = import_raw_dataset(settings, engine)
        print(json.dumps({"status": "ok", "loaded_rows": len(staged)}, ensure_ascii=False))
        return

    if args.command == "build-features":
        curated = build_curated_dataset(engine)
        print(json.dumps({"status": "ok", "feature_rows": len(curated)}, ensure_ascii=False))
        return

    if args.command == "train":
        print(json.dumps(train_models(settings, engine), ensure_ascii=False))
        return

    if args.command == "score":
        print(json.dumps(score_latest_model(settings, engine), ensure_ascii=False))
        return

    if args.command == "ensure-ready":
        counts = fetch_frame(
            engine,
            "SELECT (SELECT COUNT(*) FROM ml.training_runs WHERE selected_model = TRUE) AS selected, "
            "(SELECT COUNT(*) FROM ml.model_scores s JOIN ml.training_runs r USING (run_id) WHERE r.selected_model = TRUE) AS scores",
        ).iloc[0]
        if int(counts["selected"]) == 1 and int(counts["scores"]) == 45211:
            print(json.dumps({"status": "ready", "action": "skipped", "scored_rows": 45211}, ensure_ascii=False))
            return

    staged = import_raw_dataset(settings, engine)
    curated = build_curated_dataset(engine)
    trained = train_models(settings, engine)
    scored = score_latest_model(settings, engine)
    print(
        json.dumps(
            {
                "status": "ok",
                "loaded_rows": len(staged),
                "feature_rows": len(curated),
                "trained": trained,
                "scored": scored,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
