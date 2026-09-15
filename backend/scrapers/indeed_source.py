from backend.scrapers.base import ScrapeSource
from backend.scrapers.indeed_old import IndeedBot
from resources.enums import ScrapeStatus


class IndeedSource(ScrapeSource):
    source_name = "indeed"

    def __init__(self, headless: bool, log_callback):
        self.headless = False  # Force Indeed to open Chrome window
        self.log = log_callback
        self.bot: IndeedBot | None = None

    def run(
        self,
        keyword: str,
        location: str,
        radius: int = 25,
        fromage=0,
        scrape_mode: str = "auto",
        start_offset: int | None = None,
    ) -> list:

        self.bot = IndeedBot(
            search=keyword,
            location=location,
            radius=radius,
            date_posted=fromage, 
            headless=self.headless,
            log_callback=self.log,
        )

        if scrape_mode == "manual":
            self.log(
                f"[INFO] Indeed MANUAL mode — start offset {start_offset}"
            )
            jobs, status = self.bot.run_manual(start_offset)
        else:
            self.log("[INFO] Indeed AUTO mode enabled")
            jobs, status = self.bot.run_auto()


        if status == ScrapeStatus.CAPTCHA:
            self.log("[WARN] Indeed CAPTCHA detected — skipping Indeed results")
            return []

        for job in jobs:
            job["source"] = self.source_name

        return jobs

    def stop(self) -> None:
        if self.bot:
            self.bot.stop()
