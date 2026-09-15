from typing import List, Callable
import random
import time

from backend.scrapers.indeed_source import IndeedSource
from backend.scrapers.healthcare_source import HealthcareSource
from backend.scrapers.ziprecruiter_source import ZipRecruiterSource
from backend.scrapers.nurserecruiter_source import NurseRecruiterSource
from backend.scrapers.hospitalcareers_source import HospitalCareersSource
from backend.scrapers.healthjobsnationwide_source import HealthJobsNationwideSource


class KeywordRunner:
    def __init__(
        self,
        *,
        keywords: List[str],
        location: str,
        radius=25,
        fromage=0,
        selected_source: str = "any",
        delay_range: tuple[float, float] = (30, 60),
        headless: bool = True,
        scrape_mode: str = "auto",
        start_offset: int | None = None,
        log_callback: Callable[[str], None] = print,
    ):
        self.keywords = keywords
        self.location = location
        self.radius = radius
        self.fromage = fromage
        self.selected_source = selected_source
        self.delay_range = delay_range
        self.scrape_mode = scrape_mode
        self.start_offset = start_offset
        self.log = log_callback

        self.stop_requested = False
        self.all_jobs: list[dict] = []

        available_sources = {
            "indeed": IndeedSource(headless=headless, log_callback=self.log),
            "ziprecruiter": ZipRecruiterSource(log_callback=self.log),
            "nurserecruiter": NurseRecruiterSource(log_callback=self.log),
            "hospitalcareers": HospitalCareersSource(log_callback=self.log),
            "healthjobsnationwide": HealthJobsNationwideSource(log_callback=self.log),
            "healthcare": HealthcareSource(log_callback=self.log),
        }

        if selected_source == "any":
            # Main 3 job board sources
            source_order = [
                "healthjobsnationwide",
                "nurserecruiter",
                "ziprecruiter",
                "indeed",
            ]

            self.sources = [
                available_sources[source_name]
                for source_name in source_order
            ]
        else:
            if selected_source not in available_sources:
                raise ValueError(f"Unknown selected_source: {selected_source}")

            self.sources = [available_sources[selected_source]]

    # =====================================================
    # Control
    # =====================================================
    def stop(self) -> None:
        if self.stop_requested:
            return

        self.stop_requested = True
        self.log("[STOP] Stop requested for KeywordRunner")

        for source in self.sources:
            stop_method = getattr(source, "stop", None)

            if callable(stop_method):
                stop_method()

    def _safe_sleep(self, seconds: float) -> None:
        interval = 0.2
        loops = int(seconds / interval)

        for _ in range(loops):
            if self.stop_requested:
                return
            time.sleep(interval)

    # =====================================================
    # Main runner
    # =====================================================
    def run(self) -> list[dict]:
        self.log(f"[INFO] Active sources: {[s.source_name for s in self.sources]}")

        keywords_to_process = self.keywords

        if self.scrape_mode == "manual":
            self.log(
                f"[INFO] MANUAL mode: processing {len(keywords_to_process)} keywords "
                f"with start_offset={self.start_offset}"
            )
        else:
            self.log(
                f"[INFO] AUTO mode: processing {len(keywords_to_process)} keywords"
            )

        for index, keyword in enumerate(keywords_to_process, start=1):
            if self.stop_requested:
                break

            self.log(f"[KEYWORD_START] {index}|{len(keywords_to_process)}|{keyword}")

            jobs_before_keyword = len(self.all_jobs)

            for source in self.sources:
                if self.stop_requested:
                    break

                try:
                    self.log(f"[INFO] Source: {source.source_name}")

                    jobs = source.run(
                        keyword=keyword,
                        location=self.location,
                        radius=self.radius,
                        fromage=self.fromage,
                        scrape_mode=self.scrape_mode,
                        start_offset=self.start_offset,
                    )

                    if jobs:
                        self.all_jobs.extend(jobs)
                        self.log(
                            f"[SUCCESS] {len(jobs)} jobs from {source.source_name}"
                        )
                    else:
                        self.log(
                            f"[INFO] No jobs from {source.source_name}"
                        )

                except Exception as exc:
                    self.log(
                        f"[ERROR] {source.source_name}: {exc}"
                    )

            keyword_jobs_count = len(self.all_jobs) - jobs_before_keyword
            self.log(f"[KEYWORD_DONE] {index}|{keyword_jobs_count}")


            # Delay between keywords (AUTO mode only)
            if (
                index < len(keywords_to_process)
                and not self.stop_requested
                and self.scrape_mode == "auto"
            ):
                wait_time = random.uniform(*self.delay_range)
                self.log(f"[INFO] Waiting {wait_time:.1f}s before next keyword...")
                self._safe_sleep(wait_time)

        self.log("=" * 60)
        self.log(f"[DONE] Total jobs collected: {len(self.all_jobs)}")

        return self.all_jobs