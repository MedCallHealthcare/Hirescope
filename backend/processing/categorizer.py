"""
backend/processing/categorizer.py

Assigns healthcare verticals to jobs
based on keywords.
"""

import json
from pathlib import Path


# Load vertical keyword rules
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "verticals.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    VERTICAL_RULES = json.load(file)


def categorize_jobs(jobs: list[dict]) -> list[dict]:
    """
    Categorize jobs into healthcare verticals.

    Args:
        jobs: list of normalized job dictionaries

    Returns:
        jobs with added "vertical" field
    """

    categorized_jobs = []

    for job in jobs:

        job_title = job.get("job_title", "")
        company_name = job.get("company_name", "")
        description = job.get("description", "")

        combined_text = f"{job_title} {company_name} {description}".lower()

        assigned_vertical = "Uncategorized"

        for vertical, keywords in VERTICAL_RULES.items():

            if any(str(keyword).lower() in combined_text for keyword in keywords):
                assigned_vertical = vertical
                break

        updated_job = job.copy()
        updated_job["vertical"] = assigned_vertical

        categorized_jobs.append(updated_job)

    return categorized_jobs