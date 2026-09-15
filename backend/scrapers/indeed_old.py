# backend/scrapers/indeed_old.py

import random
import time
from datetime import datetime
from typing import Callable

from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains


from bs4 import BeautifulSoup
import ftfy

from resources.enums import ScrapeStatus


class IndeedBot:
    """
    Selenium-based Indeed scraper.
    Scrapes ONE keyword + location.
    """

    def __init__(
        self,
        *,
        search: str,
        location: str,
        radius: int = 25,
        date_posted=None,
        headless: bool = False,
        log_callback: Callable[[str], None] = print,
    ):
        self.search = search
        self.location = location
        self.radius = radius
        self.date_posted = date_posted
        self.headless = headless
        self.log = log_callback

        self.stop_requested = False
        self.driver: webdriver.Chrome | None = None

        self.base_url = (
            "https://www.indeed.com/jobs"
            f"?q={self.search}"
            f"&l={self.location}"
            f"&radius={self.radius}"
        )

        if self.date_posted not in (None, 0):
            self.base_url += f"&fromage={self.date_posted}"

    def stop(self) -> None:
        self.stop_requested = True
        self.log("[STOP] Stop requested for IndeedBot")
        self._close_driver()

    def run_auto(self, max_pages: int = 3):
        return self._run_internal(
            start_offset=0,
            max_pages=max_pages,
            manual=False,
        )

    def run_manual(self, start_offset: int):
        return self._run_internal(
            start_offset=start_offset,
            max_pages=1,
            manual=True,
        )

    def _run_internal(
        self,
        *,
        start_offset: int,
        max_pages: int,
        manual: bool,
    ):
        jobs = []

        try:
            self.driver = self._create_driver()
            wait = WebDriverWait(self.driver, 30)

            for page_index in range(max_pages):
                if self.stop_requested:
                    return jobs, ScrapeStatus.STOPPED

                offset = start_offset if manual else page_index * 10
                page_url = f"{self.base_url}&start={offset}"

                self.log(
                    f"[INFO] Scraping {'MANUAL' if manual else 'AUTO'} "
                    f"page — start={offset}"
                )

                self.driver.get(page_url)
                time.sleep(random.uniform(4.0, 6.0))

                try:
                    wait.until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "div[data-testid='slider_item']")
                        )
                    )
                except TimeoutException:
                    self.log("[ERROR] Indeed job cards were not found.")
                    self.log(f"[DEBUG] Current URL: {self.driver.current_url}")
                    time.sleep(10)
                    continue

                self._human_scroll()

                card_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[data-testid='slider_item']"
                )

                self.log(f"[INFO] Found {len(card_elements)} possible Indeed job cards")

                for index in range(len(card_elements)):
                    if self.stop_requested:
                        return jobs, ScrapeStatus.STOPPED

                    card_elements = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        "div[data-testid='slider_item']",
                    )

                    if index >= len(card_elements):
                        break

                    job = self._parse_job_card_element(card_elements[index], index)

                    if job:
                        jobs.append(job)

                self.log(f"[INFO] Parsed {len(jobs)} jobs so far")

                if manual:
                    return jobs, ScrapeStatus.OK

                self._interruptible_sleep(random.uniform(3, 6))

            return jobs, ScrapeStatus.OK

        except Exception as exc:
            self.log(f"[ERROR] Indeed scraper failed: {type(exc).__name__}: {exc}")
            self.log(
                "Either cannot find the job cards, page structure changed, "
                "or Indeed redirected the page."
            )
            return jobs, ScrapeStatus.ERROR

        finally:
            self._close_driver()

    def _create_driver(self) -> webdriver.Chrome:
        options = Options()

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)

        return driver

    def _close_driver(self) -> None:
        try:
            if self.driver:
                self.driver.quit()
        except WebDriverException:
            pass

        self.driver = None

    def _human_scroll(self) -> None:
        if not self.driver:
            return

        last_count = 0

        for _ in range(12):
            if self.stop_requested:
                return

            cards = self.driver.find_elements(
                By.CSS_SELECTOR,
                "a.jcs-JobTitle",  # Update to match new job card elements
            )

            current_count = len(cards)
            self.log(f"[SCROLL] Loaded job cards: {current_count}")

            if current_count > 0:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'end'});",
                    cards[-1],
                )
            else:
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )

            self._interruptible_sleep(random.uniform(1.5, 2.5))

            new_cards = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div[data-testid='slider_item']",
            )
            new_count = len(new_cards)

            if new_count == last_count:
                break

            last_count = new_count

    def _parse_job_card_element(self, card_element, index: int) -> dict | None:
        try:
            # Scroll the card into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card_element)
            self._interruptible_sleep(random.uniform(1.0, 2.0))

            card_html = self.driver.execute_script(
                """
                const el = arguments[0];

                const card =
                    el.closest("td.resultContent") ||
                    el.closest("div.job_seen_beacon") ||
                    el.closest("div[data-testid='slider_item']") ||
                    el;

                return card.outerHTML;
                """,
                card_element,
            )

            card = BeautifulSoup(card_html, "lxml")

            # Extract title, company, location
            title_tag = card.select_one("a.jcs-JobTitle span[id^='jobTitle-']") or card.select_one("a.jcs-JobTitle")
            company_tag = card.select_one("span[data-testid='company-name']")
            location_tag = card.select_one("div[data-testid='text-location']")
            link_tag = card.select_one("a.jcs-JobTitle")

            if not title_tag:
                return None

            job_url = None
            if link_tag and link_tag.get("href"):
                href = link_tag.get("href")
                job_url = href if href.startswith("http") else f"https://www.indeed.com{href}"

            # Extract a snippet from the card itself for description
            snippet_tag = card.select_one("div.job-snippet")
            description_text = snippet_tag.get_text(" ", strip=True) if snippet_tag else card.get_text(" ", strip=True)

            return {
                "job_title": self._clean_text(title_tag.get_text(strip=True)),
                "company_name": self._clean_text(company_tag.get_text(strip=True) if company_tag else "Unknown"),
                "location": self._clean_text(location_tag.get_text(strip=True) if location_tag else "Unknown"),
                "description": self._clean_text(description_text) if description_text else "No description available",
                "job_url": job_url,
                "search_keyword": self.search,
                "scraped_at": datetime.now().strftime("%Y-%m-%d"),
            }

        except Exception as exc:
            self.log(f"[WARN] Failed to parse Indeed card #{index + 1}: {type(exc).__name__}: {exc}")
            return None

    def _clean_text(self, text: str | None) -> str | None:
        if not text:
            return None

        return ftfy.fix_text(text)

    def _parse_job_card(self, card) -> dict | None:
        try:
            title_tag = card.select_one("span[id^='jobTitle-']")
            company_tag = card.select_one("span[data-testid='company-name']")
            location_tag = card.select_one("div[data-testid='text-location']")

            if not title_tag:
                return None

            link_tag = card.select_one("a[href*='/viewjob']") or card.select_one("a[href]")

            job_url = None
            if link_tag and link_tag.get("href"):
                href = link_tag.get("href")
                job_url = href if href.startswith("http") else f"https://www.indeed.com{href}"

            return {
                "job_title": self._clean_text(title_tag.get_text(strip=True)),
                "company_name": self._clean_text(
                    company_tag.get_text(strip=True) if company_tag else None
                ),
                "location": self._clean_text(
                    location_tag.get_text(strip=True) if location_tag else None
                ),
                "job_url": job_url,
                "search_keyword": self.search,
                "scraped_at": datetime.now().strftime("%Y-%m-%d"),
            }

        except Exception:
            return None

    def _interruptible_sleep(self, seconds: float) -> None:
        interval = 0.2
        loops = int(seconds / interval)

        for _ in range(loops):
            if self.stop_requested:
                return

            time.sleep(interval)