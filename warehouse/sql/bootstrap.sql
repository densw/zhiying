CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS curated;
CREATE SCHEMA IF NOT EXISTS ml;

CREATE TABLE IF NOT EXISTS raw.customer_campaign_contacts (
    contact_id BIGINT PRIMARY KEY,
    customer_code VARCHAR(16) NOT NULL,
    age INTEGER NOT NULL,
    job VARCHAR(64) NOT NULL,
    marital VARCHAR(32) NOT NULL,
    education VARCHAR(32) NOT NULL,
    "default" VARCHAR(8) NOT NULL,
    balance INTEGER NOT NULL,
    housing VARCHAR(8) NOT NULL,
    loan VARCHAR(8) NOT NULL,
    contact VARCHAR(32) NOT NULL,
    day INTEGER NOT NULL,
    month VARCHAR(8) NOT NULL,
    duration INTEGER NOT NULL,
    campaign INTEGER NOT NULL,
    pdays INTEGER NOT NULL,
    previous INTEGER NOT NULL,
    poutcome VARCHAR(32) NOT NULL,
    y VARCHAR(8) NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS curated.customer_features (
    contact_id BIGINT PRIMARY KEY,
    customer_code VARCHAR(16) NOT NULL,
    age INTEGER NOT NULL,
    job VARCHAR(64) NOT NULL,
    marital VARCHAR(32) NOT NULL,
    education VARCHAR(32) NOT NULL,
    "default" VARCHAR(8) NOT NULL,
    balance INTEGER NOT NULL,
    housing VARCHAR(8) NOT NULL,
    loan VARCHAR(8) NOT NULL,
    contact VARCHAR(32) NOT NULL,
    day INTEGER NOT NULL,
    month VARCHAR(8) NOT NULL,
    duration INTEGER NOT NULL,
    campaign INTEGER NOT NULL,
    pdays INTEGER NOT NULL,
    previous INTEGER NOT NULL,
    poutcome VARCHAR(32) NOT NULL,
    subscribed INTEGER NOT NULL,
    month_number INTEGER NOT NULL,
    month_name VARCHAR(8) NOT NULL,
    age_band VARCHAR(16) NOT NULL,
    balance_band VARCHAR(16) NOT NULL,
    has_prior_contact INTEGER NOT NULL,
    contact_duration_minutes DOUBLE PRECISION NOT NULL,
    campaign_intensity VARCHAR(16) NOT NULL,
    feature_built_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ml.training_runs (
    run_id VARCHAR(64) PRIMARY KEY,
    experiment_name VARCHAR(128) NOT NULL,
    model_name VARCHAR(64) NOT NULL,
    feature_version VARCHAR(64) NOT NULL,
    selected_model BOOLEAN NOT NULL DEFAULT FALSE,
    training_rows INTEGER NOT NULL,
    test_rows INTEGER NOT NULL,
    threshold DOUBLE PRECISION NOT NULL,
    roc_auc DOUBLE PRECISION NOT NULL,
    pr_auc DOUBLE PRECISION NOT NULL,
    accuracy DOUBLE PRECISION NOT NULL,
    balanced_accuracy DOUBLE PRECISION NOT NULL,
    precision DOUBLE PRECISION NOT NULL,
    recall DOUBLE PRECISION NOT NULL,
    f1 DOUBLE PRECISION NOT NULL,
    log_loss DOUBLE PRECISION NOT NULL,
    brier_score DOUBLE PRECISION NOT NULL,
    confusion_matrix_json TEXT NOT NULL,
    classification_report_text TEXT NOT NULL,
    mlflow_tracking_uri TEXT NOT NULL,
    mlflow_model_uri TEXT NOT NULL,
    model_artifact_path TEXT NOT NULL,
    report_artifact_path TEXT NOT NULL,
    trained_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ml.model_scores (
    score_id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL REFERENCES ml.training_runs(run_id),
    contact_id BIGINT NOT NULL REFERENCES curated.customer_features(contact_id),
    customer_code VARCHAR(16) NOT NULL,
    model_name VARCHAR(64) NOT NULL,
    scored_at TIMESTAMPTZ NOT NULL,
    actual_subscribed INTEGER NOT NULL,
    propensity_score DOUBLE PRECISION NOT NULL,
    priority_tier VARCHAR(16) NOT NULL,
    decile INTEGER NOT NULL CHECK (decile BETWEEN 1 AND 10),
    cumulative_capture_rate DOUBLE PRECISION NOT NULL,
    cumulative_lift DOUBLE PRECISION NOT NULL,
    UNIQUE (run_id, contact_id)
);

CREATE TABLE IF NOT EXISTS ml.model_score_deciles (
    run_id VARCHAR(64) NOT NULL REFERENCES ml.training_runs(run_id),
    decile INTEGER NOT NULL CHECK (decile BETWEEN 1 AND 10),
    prospects INTEGER NOT NULL,
    subscribers INTEGER NOT NULL,
    response_rate DOUBLE PRECISION NOT NULL,
    average_score DOUBLE PRECISION NOT NULL,
    cumulative_capture_rate DOUBLE PRECISION NOT NULL,
    cumulative_lift DOUBLE PRECISION NOT NULL,
    lift DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (run_id, decile)
);
