from backend.scrapers.base import ScrapeSource
from playwright.sync_api import sync_playwright
from datetime import datetime


CAREER_SITES = [
    {
        "company": "Citadel Healthcare",
        "url": "https://citadelhealthcare.com/careers",
        "ats": "apploi",
    },
    {
        "company": "Legacy Healthcare",
        "url": "https://legacyhc.com/careers",
        "ats": "apploi",
    },
    {
        "company": "Aperion Care",
        "url": "https://aperioncare.com/careers",
        "ats": "apploi",
    },
    {
        "company": "Belmont Village",
        "url": "https://www.belmontvillage.com/careers/careers-listing/",
        "ats": "apploi",
    },
    {
        "company": "Elevate Care",
        "url": "https://elevatecare.com/careers",
        "ats": "apploi",
    },
    {
        "company": "Ascension Living",
        "url": "https://ascensionliving.org/careers",
        "ats": "icims",
    },
    {
        "company": "Smith Senior Living",
        "url": "https://smithseniorliving.hcshiring.com/jobs",
        "ats": "hcshiring",
    },
]


class HealthcareSource(ScrapeSource):
    source_name = "healthcare_careers"

    def __init__(self, log_callback):
        self.log = log_callback
        self.stop_requested = False

    def stop(self) -> None:
        self.stop_requested = True

    def run(self, keyword: str, location: str) -> list:
        jobs = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for site in CAREER_SITES:
                if self.stop_requested:
                    break

                self.log(f"[INFO] Healthcare: {site['company']}")

                page.goto(site["url"], timeout=60000)
                page.wait_for_timeout(3000)

                links = page.query_selector_all("a")

                for link in links:
                    if self.stop_requested:
                        break

                    text = (link.inner_text() or "").lower()
                    if keyword.lower() in text:
                        jobs.append({
                            "job_title": link.inner_text().strip(),
                            "company_name": site["company"],
                            "location": location,
                            "job_url": link.get_attribute("href"),
                            "search_keyword": keyword,
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        })

            browser.close()

        self.log(f"[INFO] Healthcare collected {len(jobs)} jobs")
        return jobs
