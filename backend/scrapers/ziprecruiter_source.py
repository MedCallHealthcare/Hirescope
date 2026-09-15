import re
import time
import random
from datetime import datetime
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from backend.scrapers.base import ScrapeSource


class ZipRecruiterSource(ScrapeSource):
    source_name = "ziprecruiter"

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

        page_number = 1

        if start_offset is not None:
            page_number = int(start_offset / 10) + 1

        search_url = (
            "https://www.ziprecruiter.com/jobs-search"
            f"?search={quote_plus(keyword)}"
            f"&location={quote_plus(location)}"
        )

        if page_number > 1:
            search_url += f"&page={page_number}"

        self.log(f"[INFO] ZipRecruiter search: {search_url}")

        jobs: list[dict] = []
        seen = set()
        raw_links = []

        try:
            time.sleep(random.uniform(6.0, 10.0))

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

                self.log("[INFO] ZipRecruiter opening browser page...")

                page.goto(
                    search_url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                page.wait_for_timeout(random.randint(8000, 12000))

                # Close ZipRecruiter popup/overlay by clicking outside
                self._click_outside_ziprecruiter_popups(page)

                try:
                    page.wait_for_selector("article[id^='job-card-']", timeout=30000)
                    page.wait_for_timeout(random.randint(3000, 6000))
                except PlaywrightTimeoutError:
                    self.log("[WARN] ZipRecruiter page loaded but no job cards were detected")
                    browser.close()
                    return []

                self._click_outside_ziprecruiter_popups(page)
                self._scroll_until_all_cards_loaded(page)

                raw_links = page.locator("article[id^='job-card-']").evaluate_all(
                    """
                    cards => cards.map(card => {
                        const titleEl = card.querySelector("h2");
                        const companyEl = card.querySelector("[data-testid='job-card-company']");
                        const locationEl = card.querySelector("[data-testid='job-card-location']");

                        const links = Array.from(card.querySelectorAll("a[href]"));
                        const jobLink = links.find(a => {
                            const href = a.href || "";
                            return (
                                href.includes("ziprecruiter.com") &&
                                !href.includes("/co/") &&
                                !href.includes("jobs-search") &&
                                !href.includes("/login")
                            );
                        });

                        return {
                            cardId: card.id || "",
                            title: titleEl ? titleEl.innerText.trim() : "",
                            company: companyEl ? companyEl.innerText.trim() : "",
                            location: locationEl ? locationEl.innerText.trim() : "",
                            href: jobLink ? jobLink.href : "",
                            parentText: card.innerText || ""
                        };
                    })
                    """
                )

                self.log(f"[INFO] ZipRecruiter job cards captured: {len(raw_links)}")

                browser.close()

            for item in raw_links:
                if self.stop_requested:
                    break

                href = item.get("href", "")
                card_id = item.get("cardId", "")
                title = self._clean_text(item.get("title", ""))
                company_name = self._clean_text(item.get("company", ""))
                job_location = self._clean_text(item.get("location", "")) or location
                parent_text = self._clean_text(item.get("parentText", ""))

                if not href:
                    href = f"{search_url}#{card_id}" if card_id else search_url

                if "ziprecruiter.com" not in href:
                    continue

                if "/login" in href or "/co/" in href:
                    continue

                if href in seen:
                    continue

                if not title or len(title) < 4:
                    continue

                seen.add(href)

                jobs.append(
                    {
                        "job_title": title,
                        "company_name": company_name or "ZipRecruiter",
                        "location": job_location,
                        "job_url": href,
                        "search_keyword": keyword,
                        "description": parent_text,
                        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "source": self.source_name,
                    }
                )

        except Exception as exc:
            self.log(f"[ERROR] ZipRecruiter browser scrape failed: {exc}")
            return []

        self.log(f"[INFO] ZipRecruiter found {len(jobs)} jobs")

        return jobs

    def _scroll_until_all_cards_loaded(self, page) -> None:
        self.log("[INFO] Scrolling ZipRecruiter page to load all job cards...")

        previous_count = 0
        stable_rounds = 0
        max_scrolls = 20

        for scroll_round in range(1, max_scrolls + 1):
            if self.stop_requested:
                break

            current_count = page.locator("article[id^='job-card-']").count()
            self.log(f"[INFO] ZipRecruiter cards loaded before scroll {scroll_round}: {current_count}")

            page.mouse.wheel(0, 1800)
            page.wait_for_timeout(random.randint(1500, 2500))

            new_count = page.locator("article[id^='job-card-']").count()
            self.log(f"[INFO] ZipRecruiter cards loaded after scroll {scroll_round}: {new_count}")

            if new_count == previous_count:
                stable_rounds += 1
            else:
                stable_rounds = 0

            previous_count = new_count

            if stable_rounds >= 3:
                self.log("[INFO] ZipRecruiter card count stopped increasing")
                break

        page.mouse.wheel(0, -100000)
        page.wait_for_timeout(random.randint(1000, 2000))

        final_count = page.locator("article[id^='job-card-']").count()
        self.log(f"[INFO] ZipRecruiter final loaded card count: {final_count}")

    def _click_outside_ziprecruiter_popups(self, page) -> None:
        try:
            self.log("[INFO] Checking for ZipRecruiter popup/overlay...")

            page.wait_for_timeout(random.randint(1500, 2500))

            page.mouse.click(80, 220)
            page.wait_for_timeout(random.randint(800, 1200))

            page.mouse.click(1200, 220)
            page.wait_for_timeout(random.randint(800, 1200))

            page.keyboard.press("Escape")
            page.wait_for_timeout(random.randint(800, 1200))

            self.log("[INFO] Popup outside-click attempt completed")

        except Exception as exc:
            self.log(f"[WARN] Popup outside-click failed: {exc}")

    def stop(self) -> None:
        self.stop_requested = True

    def _slugify(self, value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"[^a-z0-9]+", "-", value)
        return value.strip("-").title().replace("-", "-")

    def _clean_text(self, value: str) -> str:
        value = re.sub(r"\s+", " ", value or "")
        return value.strip()

    def _extract_title(self, text: str, keyword: str):
        if not text:
            return None

        lines = [
            self._clean_text(line)
            for line in text.split("\n")
            if self._clean_text(line)
        ]

        keyword_lower = keyword.lower()

        for line in lines:
            line_lower = line.lower()

            if keyword_lower in line_lower:
                return line

            if any(term in line_lower for term in ["registered nurse", "rn", "lpn", "lvn", "cna"]):
                return line

        return None

    def _extract_location(self, text: str):
        match = re.search(r"\b[A-Z][a-zA-Z .'-]+,\s?[A-Z]{2}\b", text or "")
        return match.group(0) if match else None

    def _extract_company(self, text: str):
        if not text:
            return None

        parts = [p.strip() for p in re.split(r"\s{2,}|\|", text) if p.strip()]

        for part in parts:
            lower = part.lower()

            if "ziprecruiter" in lower:
                continue

            if any(word in lower for word in ["registered nurse", "nurse", "rn", "lpn", "cna"]):
                continue

            if len(part) > 2 and len(part) <= 80:
                return part

        return None