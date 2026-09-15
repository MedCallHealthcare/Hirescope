"""
backend/export/export_excel.py

Exports healthcare staffing reports
into organized Excel sheets.
"""

from pathlib import Path
import pandas as pd


EXPORT_FOLDER = Path("exports")
EXPORT_FOLDER.mkdir(exist_ok=True)


def export_excel_report(
    jobs: list[dict],
    facility_df: pd.DataFrame,
    output_path: str | Path | None = None,
    output_filename: str = "healthcare_report.xlsx"
) -> Path:
    """
    Export healthcare reports into Excel.

    Args:
        jobs: processed job dictionaries
        facility_df: grouped facility DataFrame
        output_filename: excel file name

    Returns:
        Path to generated excel file
    """

    # output_path = EXPORT_FOLDER / output_filename
    if output_path is None:
        output_path = EXPORT_FOLDER / output_filename
    else:
        output_path = Path(output_path)

    # Convert jobs to DataFrame
    jobs_df = pd.DataFrame(jobs)

    if "vertical" not in jobs_df.columns:
        jobs_df["vertical"] = "Uncategorized"

    if "score" not in jobs_df.columns:
        jobs_df["score"] = ""

    if "decision_maker_role" not in jobs_df.columns:
        jobs_df["decision_maker_role"] = ""

    # =========================
    # MERGE ZOOMINFO INTO JOBS
    # =========================

    zoominfo_columns = [
        "company_name",
        "priority",
        "zoominfo_status",
        "zoominfo_company_id",
        "zoominfo_company_name",
        "zoominfo_contact_id",
        "zoominfo_contact_name",
        "zoominfo_contact_title",
        "zoominfo_email",
        "zoominfo_phone",
        "zoominfo_mobile_phone",
        "zoominfo_management_level",
    ]

    available_zoominfo_columns = [
        column
        for column in zoominfo_columns
        if column in facility_df.columns
    ]

    if (
        not facility_df.empty
        and "company_name" in jobs_df.columns
        and available_zoominfo_columns
    ):
        zoominfo_merge_df = facility_df[
            available_zoominfo_columns
        ].copy()

        jobs_df = jobs_df.merge(
            zoominfo_merge_df,
            on="company_name",
            how="left",
        )

    # Create Excel writer
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:

        # =========================
        # VERTICAL SHEETS
        # =========================

        verticals = [
            "Acute Care",
            "Allied Health",
            "Non-Acute",
            "Educational",
            "Government",
            "Uncategorized"
        ]

        for vertical in verticals:

            vertical_df = jobs_df[
                jobs_df["vertical"] == vertical
            ]

            if not vertical_df.empty:

                sheet_name = vertical[:31]  # Excel sheet limit

                vertical_df.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False
                )

        # =========================
        # FACILITY SHEET
        # =========================

        if not facility_df.empty:

            facility_df.to_excel(
                writer,
                sheet_name="Facilities",
                index=False
            )

        # =========================
        # ZOOMINFO ENRICHMENT SHEET
        # =========================

        if not facility_df.empty:

            zoominfo_columns = [
                "company_name",
                "location",
                "priority",
                "decision_maker_roles",

                "zoominfo_status",

                "zoominfo_company_id",
                "zoominfo_company_name",

                "zoominfo_contact_id",
                "zoominfo_contact_name",
                "zoominfo_contact_title",

                "zoominfo_management_level",

                "zoominfo_email",
                "zoominfo_phone",
                "zoominfo_mobile_phone",
            ]

            available_zoominfo_columns = [
                column
                for column in zoominfo_columns
                if column in facility_df.columns
            ]

            if available_zoominfo_columns:

                zoominfo_df = facility_df[
                    available_zoominfo_columns
                ].copy()

                zoominfo_df.to_excel(
                    writer,
                    sheet_name="ZoomInfo Enrichment",
                    index=False
                )

        # =========================
        # DECISION MAKERS SHEET
        # =========================

        decision_df = jobs_df[
            [
                "company_name",
                "job_title",
                "decision_maker_role",
                "vertical",
                "score"
            ]
        ].copy()

        decision_df.to_excel(
            writer,
            sheet_name="Decision Makers",
            index=False
        )

    return output_path