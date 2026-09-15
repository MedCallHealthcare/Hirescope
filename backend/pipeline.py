"""
backend/pipeline.py

Master healthcare lead processing pipeline.
"""

from backend.processing.normalize import normalize_jobs

from backend.filter.filter_positive_keywords import (
    filter_positive_keywords
)

from backend.filter.filter_negative_keywords import (
    filter_negative_keywords
)

from backend.filter.deduplicate import deduplicate

from backend.processing.categorizer import categorize_jobs

from backend.processing.facility_classifier import (
    classify_facility_types
)

from backend.processing.scoring import score_jobs

from backend.processing.decision_maker_mapping import (
    map_decision_makers
)

from backend.processing.facility_grouping import (
    group_facilities
)

from backend.processing.priority_classifier import (
    classify_priority
)

# from backend.export.export_excel import (
#     export_excel_report
# )

from backend.zoominfo.enrichment import (
    ZoomInfoEnrichmentService
)

from backend.export.sharepoint_excel_exporter import (
    export_jobs_to_sharepoint
)


def process_healthcare_jobs(
    jobs: list[dict],
    positive_keywords: list[str],
    negative_keywords: list[str],
):
    """
    Run complete healthcare processing pipeline.
    """

    print()
    print("=" * 60)
    print("PIPELINE RECORD TRACE")
    print("=" * 60)

    original_job_count = len(jobs)

    print(f"[TRACE] Raw jobs received: {original_job_count}")

    # =========================
    # NORMALIZE
    # =========================

    jobs = normalize_jobs(jobs)

    print(f"[TRACE] After normalization: {len(jobs)}")

    # =========================
    # POSITIVE FILTER
    # =========================

    jobs, positive_removed = filter_positive_keywords(
        jobs,
        positive_keywords
    )

    print(
        f"[TRACE] After positive filter: {len(jobs)} "
        f"(removed: {positive_removed})"
    )

    # =========================
    # NEGATIVE FILTER
    # =========================

    jobs, negative_removed = filter_negative_keywords(
        jobs,
        negative_keywords
    )

    print(
        f"[TRACE] After negative filter: {len(jobs)} "
        f"(removed: {negative_removed})"
    )
    # =========================
    # DEDUPLICATE
    # =========================

    jobs_before_deduplication = len(jobs)

    jobs, blanks_removed, duplicates_removed = deduplicate(jobs)

    print(f"[TRACE] Before deduplication: {jobs_before_deduplication}")
    print(f"[TRACE] After deduplication: {len(jobs)}")
    print(f"[TRACE] Blank records removed: {blanks_removed}")
    print(f"[TRACE] Duplicate records removed: {duplicates_removed}")

    # =========================
    # CATEGORIZE
    # =========================

    jobs = categorize_jobs(jobs)

    # =========================
    # FACILITY TYPE
    # =========================

    jobs = classify_facility_types(jobs)

    # =========================
    # SCORE
    # =========================

    jobs = score_jobs(jobs)

    # =========================
    # DECISION MAKERS
    # =========================

    jobs = map_decision_makers(jobs)

    # =========================
    # FACILITY GROUPING
    # =========================

    facility_df = group_facilities(jobs)

    # =========================
    # PRIORITY CLASSIFICATION
    # =========================

    facility_df = classify_priority(facility_df)

     # =========================
    # ZOOMINFO ENRICHMENT
    # =========================

    zoominfo = ZoomInfoEnrichmentService()

    facility_df = zoominfo.enrich_facilities(
        facility_df,
        priorities=("A", "B", "C"),
        # max_facilities=5,
    )

    # =========================
    # SHAREPOINT EXCEL EXPORT
    # =========================

    print()
    print("=" * 60)
    print("SHAREPOINT EXPORT INPUT")
    print("=" * 60)

    print(f"[TRACE] Total jobs being sent to exporter: {len(jobs)}")

    for index, job in enumerate(jobs, start=1):
        print(
            f"[TRACE JOB {index}] "
            f"Title={job.get('job_title', '')!r} | "
            f"Company={job.get('company_name', '')!r} | "
            f"Location={job.get('location', '')!r} | "
            f"URL={job.get('job_url', '')!r}"
        )

    print("=" * 60)

    sharepoint_export_result = export_jobs_to_sharepoint(
        jobs
    )

    print()
    print("[TRACE] SharePoint export result:")
    print(f"        Status: {sharepoint_export_result.get('status')}")
    print(f"        Added: {sharepoint_export_result.get('added')}")
    print(f"        Duplicates: {sharepoint_export_result.get('duplicates')}")
    print(f"        Errors: {sharepoint_export_result.get('errors')}")
    print("=" * 60)

    # =========================
    # EXPORT REPORT
    # =========================

    # export_path = export_excel_report(
    #     jobs,
    #     facility_df
    # )

    # =========================
    # RETURN RESULTS
    # =========================

    return {
        "jobs": jobs,
        "facility_df": facility_df,
        "sharepoint_export": sharepoint_export_result,
        # "export_path": export_path,

        "stats": {
            "positive_removed": positive_removed,
            "negative_removed": negative_removed,
            "blanks_removed": blanks_removed,
            "duplicates_removed": duplicates_removed,
            "final_jobs": len(jobs)
        }
    }