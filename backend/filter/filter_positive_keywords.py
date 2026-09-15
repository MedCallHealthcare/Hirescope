"""
backend/filter/filter_positive_keywords.py

Keeps only jobs whose job_title OR company_name contains at least one of the
caller-supplied positive keywords (case-insensitive match).

Usage:
    from backend.filter.filter_positive_keywords import filter_positive_keywords

    positive = ["RN", "Registered Nurse", "ICU"]
    filtered, removed = filter_positive_keywords(jobs, positive)
"""

from typing import Optional


def _normalise(value: Optional[str]) -> str:
    """Lower-case + collapse whitespace."""
    if not value:
        return ""
    return " ".join(value.lower().split())


def filter_positive_keywords(
    jobs: list[dict],
    positive_keywords: list[str],
) -> tuple[list[dict], int]:
    """
    Keep only jobs that match at least one positive keyword in job_title OR company_name.

    A job is kept when ANY single positive keyword appears as a substring 
    in either job_title OR company_name (compared case-insensitively).

    Args:
        jobs:              Raw list of job dicts from the scraper.
        positive_keywords: Plain strings the caller wants to include.
                           Empty / whitespace-only strings are ignored.

    Returns:
        A tuple of:
            - filtered_jobs : list of dicts that passed the filter.
            - removed_count : how many jobs were filtered out.
    """
    # Pre-process: normalise and drop blanks once
    normalised_positives: list[str] = [
        _normalise(kw) for kw in positive_keywords if kw and kw.strip()
    ]

    # If no positive keywords, keep all jobs
    if not normalised_positives:
        return jobs, 0

    filtered_jobs: list[dict] = []

    for job in jobs:
        job_title = _normalise(job.get("job_title"))
        company = _normalise(job.get("company_name"))

        # Keep the job if ANY positive keyword is found in job_title OR company_name
        if any(pos in job_title or pos in company for pos in normalised_positives):
            filtered_jobs.append(job)

    removed_count = len(jobs) - len(filtered_jobs)
    return filtered_jobs, removed_count