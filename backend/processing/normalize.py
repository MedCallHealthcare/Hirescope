"""
backend/processing/normalize.py

Standardizes job fields for consistent filtering,
categorization, grouping, and scoring.
"""

from typing import Optional


def normalize_text(value: Optional[str]) -> str:
    """
    Normalize text by:
    - converting to lowercase
    - removing extra whitespace
    """

    if not value:
        return ""

    return " ".join(value.lower().split())


def normalize_jobs(jobs: list[dict]) -> list[dict]:
    """
    Normalize important job fields.

    Args:
        jobs: list of raw job dictionaries

    Returns:
        normalized list of jobs
    """

    normalized_jobs = []

    for job in jobs:

        normalized_job = job.copy()

        normalized_job["job_title"] = normalize_text(
            job.get("job_title") or job.get("title")
        )

        normalized_job["company_name"] = normalize_text(
            job.get("company_name") or job.get("company")
        )

        normalized_job["location"] = normalize_text(
            job.get("location")
        )

        normalized_job["description"] = normalize_text(
            job.get("description") or job.get("summary")
        )

        # Job URL
        normalized_job["job_url"] = (
            job.get("job_url")
            or job.get("url")
            or job.get("job_link")
            or ""
        ).strip()

        # Search keyword used to find the job
        normalized_job["search_keyword"] = (
            job.get("search_keyword")
            or job.get("keyword")
            or job.get("search_term")
            or ""
        ).strip()

        # Scraping source
        normalized_job["source"] = (
            job.get("source")
            or job.get("job_source")
            or ""
        ).strip()

        normalized_jobs.append(normalized_job)

    return normalized_jobs