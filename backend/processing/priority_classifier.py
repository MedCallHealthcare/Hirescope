"""
backend/processing/priority_classifier.py

Assigns A/B/C priority levels
to healthcare facilities.
"""

import pandas as pd


def classify_priority(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign facility priority classifications.

    Args:
        df: facility-level grouped DataFrame

    Returns:
        DataFrame with added priority column
    """

    if df.empty:
        return df

    df = df.copy()

    priorities = []

    for _, row in df.iterrows():

        total_score = row.get("total_score", 0)
        total_jobs = row.get("total_jobs", 0)

        # A-Level Clients
        if total_score >= 300 or total_jobs >= 20:
            priority = "A"

        # B-Level Clients
        elif total_score >= 150 or total_jobs >= 10:
            priority = "B"

        # C-Level Clients
        else:
            priority = "C"

        priorities.append(priority)

    df["priority"] = priorities

    return df