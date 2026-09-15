"""
backend/filter/deduplicate.py

Removes blank/bad job rows and duplicate jobs.

Blank/bad rows are removed when important identifying fields are empty.

Duplicate priority:
1. job_url
2. job_title + company_name + location when job_url is unavailable

Keeps the newest/latest duplicate using pandas keep="last".
"""

import pandas as pd


REQUIRED_COLUMNS = [
    "job_title",
    "company_name",
    "location",
]


def _clean_text(value):
    """
    Normalize text for duplicate checking:
    - convert None/NaN to empty string
    - lowercase
    - trim spaces
    - collapse multiple spaces
    """
    if pd.isna(value):
        return ""

    return " ".join(str(value).lower().strip().split())


def _normalize_url(value):
    """
    Normalize a job URL for duplicate checking.
    """
    if pd.isna(value) or not value:
        return ""

    return str(value).strip().lower().rstrip("/")


def _create_fallback_key(row):
    """
    Create a fallback duplicate key using the job's
    identifying text fields.
    """

    job_title = _clean_text(row.get("job_title"))
    company_name = _clean_text(row.get("company_name"))
    location = _clean_text(row.get("location"))

    return (
        f"fallback::{job_title}|"
        f"{company_name}|"
        f"{location}"
    )


def _create_unique_key(row, shared_urls=None):
    """
    Create a duplicate key.

    Priority:
    1. Use job_url when it appears to belong to one job.
    2. If the same URL is being shared by multiple different jobs,
       use job_title + company_name + location instead.
    3. If job_url is unavailable, use the fallback key.
    """

    if shared_urls is None:
        shared_urls = set()

    job_url = _normalize_url(row.get("job_url"))

    if job_url and job_url not in shared_urls:
        return f"url::{job_url}"

    return _create_fallback_key(row)


def deduplicate(jobs: list[dict]) -> tuple[list[dict], int, int]:
    """
    Remove blank/bad rows and duplicate jobs using pandas.

    Args:
        jobs: Raw list of job dictionaries.

    Returns:
        A tuple of:
            - cleaned_jobs: list of dicts after blank removal and deduplication
            - blanks_removed: number of blank/bad rows removed
            - duplicates_removed: number of duplicate rows removed
    """

    if not jobs:
        return [], 0, 0

    df = pd.DataFrame(jobs)

    starting_count = len(df)

    # Make sure required columns exist
    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    # job_url is optional, but the column must exist
    # so alternative URL fields can be mapped into it.
    if "job_url" not in df.columns:
        df["job_url"] = ""

    # Clean job_url before checking alternative URL fields.
    df["job_url"] = (
        df["job_url"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Support alternative URL fields from other job boards.
    if "url" in df.columns:
        alternative_url = (
            df["url"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df["job_url"] = df["job_url"].where(
            df["job_url"] != "",
            alternative_url
        )

    if "apply_url" in df.columns:
        alternative_url = (
            df["apply_url"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df["job_url"] = df["job_url"].where(
            df["job_url"] != "",
            alternative_url
        )

    if "source_url" in df.columns:
        alternative_url = (
            df["source_url"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df["job_url"] = df["job_url"].where(
            df["job_url"] != "",
            alternative_url
        )

    # Convert required fields to cleaned strings.
    for column in REQUIRED_COLUMNS:
        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # Remove bad Indeed URL rows like:
    # https://www.indeed.com#
    if "job_url" in df.columns:
        df["job_url"] = df["job_url"].replace("https://www.indeed.com#", "")

    # Remove rows where essential identifying fields are blank.
    #
    # job_url is optional because some job boards may return
    # valid jobs without a URL.
    df = df[
        (df["job_title"] != "") &
        (df["company_name"] != "") &
        (df["location"] != "")
    ]

    after_blank_removal_count = len(df)
    blanks_removed = starting_count - after_blank_removal_count

    # =========================
    # BUILD DUPLICATE KEYS
    # =========================

    # Normalize URLs first so we can detect URLs that are
    # incorrectly shared by multiple different jobs.
    df["_normalized_job_url"] = df["job_url"].apply(
        _normalize_url
    )

    # Create the fallback identity for every job.
    df["_fallback_key"] = df.apply(
        _create_fallback_key,
        axis=1
    )

    # Find URLs that are being used by more than one
    # DIFFERENT job.
    #
    # Example:
    #
    # Same URL + Registered Nurse + Hospital A
    # Same URL + Medical Assistant + Hospital B
    #
    # In that situation, the URL should NOT be trusted
    # as the duplicate key.
    url_identity_counts = (
        df[df["_normalized_job_url"] != ""]
        .groupby("_normalized_job_url")["_fallback_key"]
        .nunique()
    )

    shared_urls = set(
        url_identity_counts[
            url_identity_counts > 1
        ].index
    )

    print()
    print("[DEDUP DEBUG]")
    print(f"Records before deduplication: {len(df)}")
    print(f"Suspicious shared URLs found: {len(shared_urls)}")

    if shared_urls:
        print(
            "[DEDUP DEBUG] These URLs are associated "
            "with multiple different jobs:"
        )

        for url in shared_urls:
            matching_jobs = df[
                df["_normalized_job_url"] == url
            ]

            print(f"  URL: {url}")
            print(f"  Different jobs using URL: {len(matching_jobs)}")

            for _, matching_job in matching_jobs.iterrows():
                print(
                    "     - "
                    f"{matching_job.get('job_title', '')} | "
                    f"{matching_job.get('company_name', '')} | "
                    f"{matching_job.get('location', '')}"
                )

    # Create the final duplicate key.
    df["_duplicate_key"] = df.apply(
        lambda row: _create_unique_key(
            row,
            shared_urls
        ),
        axis=1
    )

    before_deduplication_count = len(df)

    # Remove duplicates and keep the latest occurrence.
    df = df.drop_duplicates(
        subset=["_duplicate_key"],
        keep="last"
    )

    after_deduplication_count = len(df)

    # Calculate how many duplicate records were removed.
    duplicates_removed = (
        before_deduplication_count - after_deduplication_count
    )

    print(f"[DEDUP DEBUG] Records after deduplication: {after_deduplication_count}")
    print(f"[DEDUP DEBUG] Duplicates removed: {duplicates_removed}")
    print(f"[DEDUP DEBUG] Blank/bad rows removed: {blanks_removed}")

    # Remove temporary duplicate-checking column.
    df = df.drop(
        columns=[
            "_duplicate_key",
            "_normalized_job_url",
            "_fallback_key",
        ],
        errors="ignore"
    )

    cleaned_jobs = df.to_dict(orient="records")

    return cleaned_jobs, blanks_removed, duplicates_removed