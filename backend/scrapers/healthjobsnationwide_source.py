import re
import time
import random
from datetime import datetime
from urllib.parse import quote_plus, urljoin

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from backend.scrapers.base import ScrapeSource


class HealthJobsNationwideSource(ScrapeSource):
    source_name = "healthjobsnationwide"

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
        seen = set()

        search_url = (
            "https://www.healthjobsnationwide.com/jobs"
            f"?search={quote_plus(keyword)}"
            f"&job_geo_location={quote_plus(location + ', USA')}"
            f"&radius=160.94"
            f"&Find+Jobs=Find+Jobs"
        )

        self.log(f"[INFO] HealthJobsNationwide search: {search_url}")

        try:
            time.sleep(random.uniform(3.0, 6.0))

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)

                page = browser.new_page(
                    viewport={"width": 1366, "height": 768},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0 Safari/537.36"
                    ),
                )

                self.log("[INFO] HealthJobsNationwide opening browser page...")

                page.goto(
                    search_url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                page.wait_for_timeout(random.randint(6000, 9000))

                try:
                    page.wait_for_selector("article.node--job-per-template", timeout=30000)
                except PlaywrightTimeoutError:
                    self.log("[WARN] HealthJobsNationwide page loaded but no job cards were detected")
                    browser.close()
                    return []

                for _ in range(5):
                    page.mouse.wheel(0, 900)
                    page.wait_for_timeout(random.randint(800, 1500))

                raw_cards = page.locator("article.node--job-per-template").evaluate_all(
                    """
                    cards => cards.map(card => {
                        const titleLink = card.querySelector("a.recruiter-job-link");

                        return {
                            title: titleLink ? titleLink.innerText.trim() : "",
                            href: titleLink ? titleLink.href : "",
                            text: card.innerText || ""
                        };
                    })
                    """
                )

                browser.close()

        except Exception as exc:
            self.log(f"[ERROR] HealthJobsNationwide browser scrape failed: {exc}")
            return []

        self.log(f"[INFO] HealthJobsNationwide job cards detected: {len(raw_cards)}")

        for card in raw_cards:
            if self.stop_requested:
                break

            title = self._clean_text(card.get("title", ""))
            href = card.get("href", "").strip()
            if not title or len(title) < 4:
                continue

            if not href:
                continue

            job_url = urljoin("https://www.healthjobsnationwide.com", href)

            if job_url in seen:
                continue

            seen.add(job_url)

            card_text = self._clean_text(card.get("text", ""))

            company_name = self._extract_company(card_text)
            job_location = self._extract_location(card_text) or location

            jobs.append(
                {
                    "job_title": title,
                    "company_name": company_name or "HealthJobsNationwide",
                    "location": job_location,
                    "job_url": job_url,
                    "search_keyword": keyword,
                    "description": card_text,
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": self.source_name,
                }
            )

        self.log(f"[INFO] HealthJobsNationwide found {len(jobs)} jobs")

        return jobs

    def stop(self) -> None:
        self.stop_requested = True

    def _clean_text(self, value: str) -> str:
        value = re.sub(r"\s+", " ", value or "")
        return value.strip()

    def _extract_location(self, text: str):
        match = re.search(r"\b[A-Z][a-zA-Z .'-]+,\s?[A-Z]{2}\b", text or "")
        return match.group(0) if match else None

    def _extract_company(self, text: str):
        if not text:
            return None

        parts = [
            self._clean_text(part)
            for part in re.split(r"\s{2,}|\n|\|", text)
            if self._clean_text(part)
        ]

        skip_terms = [
            "featured",
            "nurse practitioner",
            "physician assistant",
            "physician",
            "registered nurse",
            "rn",
            "lpn",
            "cna",
        ]

        for part in parts:
            lower = part.lower()

            if any(term in lower for term in skip_terms):
                continue

            if re.search(r"\b\d{2}/\d{2}/\d{4}\b", part):
                continue

            if re.search(r"\b[A-Z][a-zA-Z .'-]+,\s?[A-Z]{2}\b", part):
                continue

            if 2 < len(part) <= 80:
                return part

        return None