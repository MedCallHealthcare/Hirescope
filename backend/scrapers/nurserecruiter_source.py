import re
import time
import random
from datetime import datetime
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from backend.scrapers.base import ScrapeSource


class NurseRecruiterSource(ScrapeSource):
    source_name = "nurserecruiter"

    def __init__(self, log_callback):
        self.log = log_callback
        self.stop_requested = False

    def run(
        self,
        keyword: str,
        location: str,
        radius: int = 25,
        fromage=0,
        scrape_mode: str = "auto",
        start_offset: int | None = None,
    ) -> list[dict]:

        self.stop_requested = False

        jobs: list[dict] = []

        search_url = (
            "https://www.nurserecruiter.com/jobs"
            f"?q={quote_plus(keyword)}"
            f"&location={quote_plus(location)}"
        )

        self.log(f"[INFO] NurseRecruiter search: {search_url}")

        try:
            time.sleep(random.uniform(2.5, 5.0))

            response = requests.get(
                search_url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept-Language": "en-US,en;q=0.9",
                },
                timeout=30,
            )

            if response.status_code in [403, 429]:
                self.log(
                    f"[WARN] NurseRecruiter blocked or rate-limited request: "
                    f"{response.status_code}"
                )
                return []

            response.raise_for_status()

        except Exception as exc:
            self.log(f"[ERROR] NurseRecruiter request failed: {exc}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        job_links = []

        for link in soup.find_all("a", href=True):
            if self.stop_requested:
                break

            text = link.get_text(" ", strip=True)
            href = link.get("href", "")

            if not text or len(text) < 4:
                continue

            combined_text = text.lower()
            keyword_lower = keyword.lower()

            healthcare_terms = [
                "nurse",
                "rn",
                "lpn",
                "lvn",
                "cna",
                "registered nurse",
                "licensed practical nurse",
                "nursing",
                "icu",
                "er",
                "med surg",
                "telemetry",
                "dialysis",
                "home health",
            ]

            if keyword_lower not in combined_text and not any(
                term in combined_text for term in healthcare_terms
            ):
                continue

            if href.startswith("/"):
                href = "https://www.nurserecruiter.com" + href

            if "nurserecruiter.com" not in href:
                continue

            job_links.append((text, href))

        seen = set()

        for title, url in job_links:
            if self.stop_requested:
                break

            if url in seen:
                continue

            seen.add(url)

            jobs.append(
                {
                    "job_title": self._clean_text(title),
                    "company_name": "NurseRecruiter",
                    "location": location,
                    "job_url": url,
                    "search_keyword": keyword,
                    "description": "",
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": self.source_name,
                }
            )

        self.log(f"[INFO] NurseRecruiter found {len(jobs)} jobs")

        return jobs

    def stop(self) -> None:
        self.stop_requested = True

    def _clean_text(self, value: str) -> str:
        value = re.sub(r"\s+", " ", value or "")
        return value.strip()