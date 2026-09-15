"""
backend/processing/scoring.py

Scores healthcare staffing jobs
based on configurable keyword rules.
"""

import json
from pathlib import Path


# Load scoring rules
CONFIG_PATH = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "scoring_rules.json"
)

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    SCORING_RULES = json.load(file)


def score_jobs(jobs: list[dict]) -> list[dict]:
    """
    Assign scores to jobs based on keyword matches.

    Args:
        jobs: list of categorized job dictionaries

    Returns:
        jobs with added:
            - score
            - matched_scoring_keywords
    """

    scored_jobs = []

    for job in jobs:

        description = job.get("description", "")
        job_title = job.get("job_title", "")
        company_name = job.get("company_name", "")

        combined_text = (
            f"{job_title} "
            f"{company_name} "
            f"{description}"
        )

        score = 0
        matched_keywords = []

        # Apply scoring rules
        for keyword, points in SCORING_RULES.items():

            if keyword in combined_text:
                score += points
                matched_keywords.append(keyword)

        updated_job = job.copy()

        updated_job["score"] = score
        updated_job["matched_scoring_keywords"] = matched_keywords

        scored_jobs.append(updated_job)

    return scored_jobs