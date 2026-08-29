import os


POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "zhiying")
POSTGRES_USER = os.getenv("POSTGRES_USER", "zhiying")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "zhiying_local_pwd")

SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "replace_me_with_a_long_secret")
TALISMAN_ENABLED = False
WTF_CSRF_ENABLED = True
FEATURE_FLAGS = {
    "DASHBOARD_RBAC": True,
}
