"""
backend/processing/facility_grouping.py

Groups healthcare jobs by facility/company
to generate facility-level intelligence.
"""

import pandas as pd


def _mode_or_first(series):
    """
    Return the most common non-empty value.
    If there is no mode, return the first non-empty value.
    """

    values = series.dropna().astype(str)
    values = values[values.str.strip() != ""]

    if values.empty:
        return ""

    mode = values.mode()

    if not mode.empty:
        return mode.iloc[0]

    return values.iloc[0]


def _unique_values(series):
    """
    Combine unique non-empty values into one string.
    """

    values = []

    for value in series.dropna():
        value = str(value).strip()

        if value and value not in values:
            values.append(value)

    return "; ".join(values)


def group_facilities(jobs: list[dict]) -> pd.DataFrame:
    """
    Group jobs by company/facility.

    Args:
        jobs: list of scored job dictionaries

    Returns:
        DataFrame containing facility intelligence
    """

    if not jobs:
        return pd.DataFrame()

    df = pd.DataFrame(jobs)

    required_columns = [
        "company_name",
        "job_title",
        "vertical",
        "score",
        "posted_date",
        "location",
        "decision_maker_role",
        "decision_maker_roles",
        "website",
        "job_url",
    ]

    for column in required_columns:
        if column not in df.columns:
            df[column] = ""

    grouped = (
        df.groupby("company_name", dropna=False)
        .agg(
            location=("location", _mode_or_first),
            website=("website", _mode_or_first),

            decision_maker_roles=(
                "decision_maker_roles",
                _unique_values
            ),

            total_jobs=("job_title", "count"),

            total_score=("score", "sum"),

            average_score=("score", "mean"),

            unique_job_titles=("job_title", "nunique"),

            top_vertical=(
                "vertical",
                _mode_or_first
            ),

            latest_posted_date=(
                "posted_date",
                "max"
            ),

            sample_job_url=(
                "job_url",
                _mode_or_first
            ),
        )
        .reset_index()
    )

    grouped["average_score"] = (
        grouped["average_score"]
        .round(2)
    )

    grouped = grouped.sort_values(
        by=[
            "total_score",
            "total_jobs"
        ],
        ascending=False
    )

    return grouped