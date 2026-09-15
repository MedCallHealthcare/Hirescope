"""
backend/processing/decision_maker_mapping.py

Maps healthcare jobs to likely decision-maker roles.
"""

import json
from pathlib import Path


CONFIG_PATH = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "decision_makers.json"
)

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    DECISION_MAKER_RULES = json.load(file)


DEFAULT_FALLBACK_ROLES = [
    "Chief Human Resources Officer",
    "Human Resources Director",
    "Talent Acquisition Director",
    "Recruiting Manager",
    "Human Resources Manager",
]


ROLE_FALLBACKS = {
    "emergency": [
        "Emergency Department Director",
        "Director of Emergency Services",
        "Director of Nursing",
        "Chief Nursing Officer",
    ],

    "nursing": [
        "Chief Nursing Officer",
        "Director of Nursing",
        "Nursing Director",
    ],

    "staffing": [
        "Staffing Manager",
        "Recruiting Manager",
        "Talent Acquisition Manager",
        "Human Resources Director",
    ],

    "human resources": [
        "Chief Human Resources Officer",
        "Human Resources Director",
        "Human Resources Manager",
    ],

    "recruit": [
        "Talent Acquisition Director",
        "Recruiting Director",
        "Recruiting Manager",
        "Recruiter",
    ],
}


def _get_fallback_roles(text: str) -> list[str]:
    """
    Return likely fallback decision makers
    based on job context.
    """

    text = text.lower()

    for keyword, roles in ROLE_FALLBACKS.items():
        if keyword in text:
            return roles

    return DEFAULT_FALLBACK_ROLES


def map_decision_makers(
    jobs: list[dict]
) -> list[dict]:
    """
    Assign likely decision-maker roles to jobs.

    Adds:
        decision_maker_role
        decision_maker_roles
    """

    mapped_jobs = []

    for job in jobs:

        job_title = str(
            job.get("job_title", "")
        ).strip()

        description = str(
            job.get("description", "")
        ).strip()

        combined_text = (
            f"{job_title} {description}"
        ).lower()

        matched_roles = []

        # =========================
        # CONFIG RULE MATCHING
        # =========================

        for keyword, role in (
            DECISION_MAKER_RULES.items()
        ):

            keyword_lower = str(
                keyword
            ).lower().strip()

            if (
                keyword_lower
                and keyword_lower
                in combined_text
            ):
                if role not in matched_roles:
                    matched_roles.append(role)

        # =========================
        # FALLBACK
        # =========================

        if not matched_roles:
            matched_roles = (
                _get_fallback_roles(
                    combined_text
                )
            )

        updated_job = job.copy()

        # Keep existing field
        # for compatibility.
        updated_job[
            "decision_maker_role"
        ] = matched_roles[0]

        # New field containing
        # multiple useful targets.
        updated_job[
            "decision_maker_roles"
        ] = "; ".join(
            matched_roles
        )

        mapped_jobs.append(
            updated_job
        )

    return mapped_jobs