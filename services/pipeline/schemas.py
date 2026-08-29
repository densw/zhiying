from __future__ import annotations

import pandera as pa
from pandera import Check, Column, DataFrameSchema


MONTH_KEYS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


STAGED_RAW_SCHEMA = DataFrameSchema(
    {
        "contact_id": Column(int, Check.greater_than(0), unique=True, nullable=False),
        "customer_code": Column(str, Check.str_matches(r"^KH\d{6}$"), nullable=False),
        "age": Column(int, Check.in_range(18, 100), nullable=False),
        "job": Column(str, nullable=False),
        "marital": Column(str, nullable=False),
        "education": Column(str, nullable=False),
        "default": Column(str, Check.isin(["yes", "no"]), nullable=False),
        "balance": Column(int, nullable=False),
        "housing": Column(str, Check.isin(["yes", "no"]), nullable=False),
        "loan": Column(str, Check.isin(["yes", "no"]), nullable=False),
        "contact": Column(str, nullable=False),
        "day": Column(int, Check.in_range(1, 31), nullable=False),
        "month": Column(str, Check.isin(MONTH_KEYS), nullable=False),
        "duration": Column(int, Check.greater_than_or_equal_to(0), nullable=False),
        "campaign": Column(int, Check.greater_than(0), nullable=False),
        "pdays": Column(int, Check.greater_than_or_equal_to(-1), nullable=False),
        "previous": Column(int, Check.greater_than_or_equal_to(0), nullable=False),
        "poutcome": Column(str, nullable=False),
        "y": Column(str, Check.isin(["yes", "no"]), nullable=False),
    },
    coerce=True,
    strict=True,
)

CURATED_SCHEMA = DataFrameSchema(
    {
        "contact_id": Column(int, Check.greater_than(0), unique=True, nullable=False),
        "customer_code": Column(str, Check.str_matches(r"^KH\d{6}$"), nullable=False),
        "age": Column(int, Check.in_range(18, 100), nullable=False),
        "job": Column(str, nullable=False),
        "marital": Column(str, nullable=False),
        "education": Column(str, nullable=False),
        "default": Column(str, Check.isin(["yes", "no"]), nullable=False),
        "balance": Column(int, nullable=False),
        "housing": Column(str, Check.isin(["yes", "no"]), nullable=False),
        "loan": Column(str, Check.isin(["yes", "no"]), nullable=False),
        "contact": Column(str, nullable=False),
        "day": Column(int, Check.in_range(1, 31), nullable=False),
        "month": Column(str, Check.isin(MONTH_KEYS), nullable=False),
        "duration": Column(int, Check.greater_than_or_equal_to(0), nullable=False),
        "campaign": Column(int, Check.greater_than(0), nullable=False),
        "pdays": Column(int, Check.greater_than_or_equal_to(-1), nullable=False),
        "previous": Column(int, Check.greater_than_or_equal_to(0), nullable=False),
        "poutcome": Column(str, nullable=False),
        "subscribed": Column(int, Check.isin([0, 1]), nullable=False),
        "month_number": Column(int, Check.in_range(1, 12), nullable=False),
        "month_name": Column(str, nullable=False),
        "age_band": Column(str, nullable=False),
        "balance_band": Column(str, nullable=False),
        "has_prior_contact": Column(int, Check.isin([0, 1]), nullable=False),
        "contact_duration_minutes": Column(float, Check.greater_than_or_equal_to(0), nullable=False),
        "campaign_intensity": Column(str, nullable=False),
    },
    coerce=True,
    strict=True,
)


def validate_staged_raw(frame):
    return STAGED_RAW_SCHEMA.validate(frame, lazy=True)


def validate_curated(frame):
    return CURATED_SCHEMA.validate(frame, lazy=True)
