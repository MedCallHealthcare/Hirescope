"""
backend/processing/facility_classifier.py

Classifies healthcare jobs by facility type.
"""


FACILITY_TYPE_RULES = {
    "Hospice": [
        "hospice",
        "hospice care",
        "palliative care",
        "end of life care",
        "end-of-life care",
    ],

    "Veterans Home": [
        "veterans home",
        "veteran home",
        "state veterans home",
        "va nursing home",
        "veterans nursing home",
    ],

    "Nursing Home": [
        "nursing home",
        "skilled nursing facility",
        "skilled nursing center",
        "skilled nursing centre",
        "skilled nursing",
        "snf",
    ],

    "Long-Term Care": [
        "long term care",
        "long-term care",
        "longterm care",
        "ltc",
        "extended care facility",
        "extended care center",
        "extended care centre",
    ],

    "Hospital": [
        "hospital",
        "medical center",
        "medical centre",
        "health system",
        "healthcare system",
    ],
}


def classify_facility_types(jobs: list[dict]) -> list[dict]:
    classified_jobs = []

    for job in jobs:
        company_name = str(job.get("company_name", ""))
        job_title = str(job.get("job_title", ""))
        description = str(job.get("description", ""))

        combined_text = " ".join(
            f"{company_name} {job_title} {description}"
            .lower()
            .replace("-", " ")
            .split()
        )

        searchable_text = f" {combined_text} "

        facility_type = "Other"

        for type_name, keywords in FACILITY_TYPE_RULES.items():
            matched = any(
                f" {' '.join(keyword.lower().replace('-', ' ').split())} "
                in searchable_text
                for keyword in keywords
            )

            if matched:
                facility_type = type_name
                break

        updated_job = job.copy()
        updated_job["facility_type"] = facility_type

        classified_jobs.append(updated_job)

    return classified_jobs