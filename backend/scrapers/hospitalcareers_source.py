import re
import time
import random
from datetime import datetime
from urllib.parse import quote_plus, urljoin

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from backend.scrapers.base import ScrapeSource


class HospitalCareersSource(ScrapeSource):
    source_name = "hospitalcareers"

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
            "https://hospitalcareers.com/jobs/"
            f"?q={quote_plus(keyword)}"
            f"&l={quote_plus(location)}"
        )

        self.log(f"[INFO] HospitalCareers search: {search_url}")

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

                self.log("[INFO] HospitalCareers opening browser page...")

                page.goto(
                    search_url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                page.wait_for_timeout(random.randint(6000, 9000))

                try:
                    page.wait_for_selector("article.listing-item__jobs", timeout=30000)
                except PlaywrightTimeoutError:
                    self.log("[WARN] HospitalCareers page loaded but no job cards were detected")
                    browser.close()
                    return []

                for _ in range(5):
                    page.mouse.wheel(0, 900)
                    page.wait_for_timeout(random.randint(800, 1500))

                raw_cards = page.locator("article.listing-item__jobs").evaluate_all(
                    """
                    cards => cards.map(card => {
                        const titleLink = card.querySelector("a.link");
                        const companyEl = card.querySelector(".listing-item__info--item-company");
                        const locationEl = card.querySelector(".listing-item__info--item-location");

                        return {
                            title: titleLink ? titleLink.innerText.trim() : "",
                            href: titleLink ? titleLink.href : "",
                            company: companyEl ? companyEl.innerText.trim() : "",
                            location: locationEl ? locationEl.innerText.trim() : "",
                            description: card.innerText || ""
                        };
                    })
                    """
                )

                browser.close()

        except Exception as exc:
            self.log(f"[ERROR] HospitalCareers browser scrape failed: {exc}")
            return []

        self.log(f"[INFO] HospitalCareers job cards detected: {len(raw_cards)}")

        for card in raw_cards:
            if self.stop_requested:
                break

            title = self._clean_text(card.get("title", ""))
            href = card.get("href", "").strip()

            if not title or len(title) < 4:
                continue

            if not href:
                continue

            job_url = urljoin("https://hospitalcareers.com", href)

            if job_url in seen:
                continue

            seen.add(job_url)

            company_name = self._clean_text(card.get("company", ""))
            job_location = self._clean_text(card.get("location", "")) or location
            description = self._clean_text(card.get("description", ""))

            jobs.append(
                {
                    "job_title": title,
                    "company_name": company_name or "HospitalCareers",
                    "location": job_location,
                    "job_url": job_url,
                    "search_keyword": keyword,
                    "description": description,
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": self.source_name,
                }
            )

        self.log(f"[INFO] HospitalCareers found {len(jobs)} jobs")

        return jobs

    def stop(self) -> None:
        self.stop_requested = True

    def _clean_text(self, value: str) -> str:
        value = re.sub(r"\s+", " ", value or "")
        return value.strip()