"""
backend/filter/filter_negative_keywords.py

Removes jobs whose company_name OR job_title contains any of the
caller-supplied negative keywords (case-insensitive match).

Usage:
    from backend.filter.filter_negative_keywords import filter_negative_keywords

    negative = ["Advocate Health", "Ascension", "Advanced Practice Provider"]
    cleaned, removed = filter_negative_keywords(jobs, negative)
"""

from typing import Optional


def _normalise(value: Optional[str]) -> str:
    """Lower-case + collapse whitespace."""
    if not value:
        return ""
    return " ".join(value.lower().split())


def filter_negative_keywords(
    jobs: list[dict],
    negative_keywords: list[str],
) -> tuple[list[dict], int]:
    """
    Remove jobs that match any negative keyword in company_name OR job_title.

    A job is removed when ANY single negative keyword appears as a
    substring of company_name OR job_title (compared case-insensitively).

    Args:
        jobs:              Raw list of job dicts from the scraper.
        negative_keywords: Plain strings the caller wants to exclude.
                           Empty / whitespace-only strings are ignored.

    Returns:
        A tuple of:
            - filtered_jobs : list of dicts that passed the filter.
            - removed_count : how many jobs were filtered out.
    """
    # Pre-process: normalise and drop blanks once
    normalised_negatives: list[str] = [
        _normalise(kw) for kw in negative_keywords if kw and kw.strip()
    ]

    # Nothing to filter
    if not normalised_negatives:
        return jobs, 0

    filtered_jobs: list[dict] = []

    for job in jobs:
        company = _normalise(job.get("company_name"))
        job_title = _normalise(job.get("job_title"))

        # Keep the job only if NO negative keyword is found in company_name OR job_title
        if not any(neg in company or neg in job_title for neg in normalised_negatives):
            filtered_jobs.append(job)

    removed_count = len(jobs) - len(filtered_jobs)
    return filtered_jobs, removed_count