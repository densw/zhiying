from __future__ import annotations

import os

FEATURE_FLAGS = {
    "DASHBOARD_RBAC": True,
}

APP_NAME = "经营分析中心"
LOGO_TARGET_PATH = "/superset/welcome/"

SQLALCHEMY_DATABASE_URI = os.getenv(
    "SUPERSET_METADATA_URI",
    "postgresql+psycopg2://zhiying:zhiying_local_pwd@postgres:5432/superset",
)
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "replace_me_with_a_long_secret")

SQLLAB_CTAS_NO_LIMIT = True
WTF_CSRF_ENABLED = False

ENABLE_PROXY_FIX = True
