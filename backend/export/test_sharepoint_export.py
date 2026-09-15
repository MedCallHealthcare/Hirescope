from datetime import datetime

from sharepoint_excel_exporter import export_jobs_to_sharepoint


def print_results(test_name, results):
    print()
    print("=" * 60)
    print(test_name)
    print("=" * 60)
    print(f"Status:     {results['status']}")
    print(f"Added:      {results['added']}")
    print(f"Duplicates: {results['duplicates']}")
    print(f"Errors:     {results['errors']}")
    print(f"Attempts:   {results['attempts']}")
    print(f"Message:    {results['message']}")
    print()


if __name__ == "__main__":

    # Create a unique ID every time this test script starts.
    #
    # This prevents records from an older test run from
    # interfering with the current controlled test.
    test_id = datetime.now().strftime("%Y%m%d%H%M%S")

    print()
    print("=" * 60)
    print("SHAREPOINT EXPORT CONTROLLED TEST")
    print("=" * 60)
    print(f"Test ID: {test_id}")
    print()

    # =========================================================
    # TEST 1
    # Export two completely new records.
    # Expected:
    # Added = 2
    # Duplicates = 0
    # =========================================================

    test_1_jobs = [
        {
            "job_title": f"Registered Nurse CONTROLLED {test_id}",
            "company_name": "MedCall Test Hospital",
            "location": "Chicago, IL",
            "job_url": (
                f"https://example.com/"
                f"controlled-rn-{test_id}"
            ),
            "search_keyword": "Registered Nurse",
            "source": "SharePoint Controlled Test",
        },
        {
            "job_title": f"Director of Nursing CONTROLLED {test_id}",
            "company_name": "MedCall Test Skilled Nursing Facility",
            "location": "Dallas, TX",
            "job_url": (
                f"https://example.com/"
                f"controlled-don-{test_id}"
            ),
            "search_keyword": "Director of Nursing",
            "source": "SharePoint Controlled Test",
        },
    ]

    print("Running TEST 1: New records...")

    test_1_results = export_jobs_to_sharepoint(
        test_1_jobs
    )

    print_results(
        "TEST 1 RESULTS - NEW RECORDS",
        test_1_results,
    )

    if (
        test_1_results["added"] == 2
        and test_1_results["duplicates"] == 0
        and test_1_results["status"] == "success"
    ):
        print("TEST 1: PASSED")
    else:
        print("TEST 1: FAILED")

    # =========================================================
    # TEST 2
    # Export the exact same records again.
    #
    # Expected:
    # Added = 0
    # Duplicates = 2
    # Status = no_changes
    # =========================================================

    print()
    print("Running TEST 2: Existing duplicate records...")

    test_2_results = export_jobs_to_sharepoint(
        test_1_jobs
    )

    print_results(
        "TEST 2 RESULTS - EXISTING DUPLICATES",
        test_2_results,
    )

    if (
        test_2_results["added"] == 0
        and test_2_results["duplicates"] == 2
        and test_2_results["status"] == "no_changes"
    ):
        print("TEST 2: PASSED")
    else:
        print("TEST 2: FAILED")

    # =========================================================
    # FINAL PRODUCTION TEST SUMMARY
    # =========================================================

    test_1_passed = (
        test_1_results["added"] == 2
        and test_1_results["duplicates"] == 0
        and test_1_results["status"] == "success"
    )

    test_2_passed = (
        test_2_results["added"] == 0
        and test_2_results["duplicates"] == 2
        and test_2_results["status"] == "no_changes"
    )

    print()
    print("=" * 60)
    print("PRODUCTION CONTROLLED TEST SUMMARY")
    print("=" * 60)

    if test_1_passed and test_2_passed:
        print("RESULT: PRODUCTION EXPORT TEST PASSED")
        print("2 new records were added successfully.")
        print("The same 2 records were detected as duplicates.")
    else:
        print("RESULT: PRODUCTION EXPORT TEST FAILED")
        print("Do NOT run the full scraper yet.")

    print("=" * 60)