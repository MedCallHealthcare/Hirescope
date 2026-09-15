from abc import ABC, abstractmethod
from typing import List


class ScrapeSource(ABC):
    source_name: str = "base"

    @abstractmethod
    def run(
        self,
        keyword: str,
        location: str,
        radius: int = 25,
        fromage: int = 0,
        scrape_mode: str = "auto",
        start_offset: int | None = None,
    ) -> List[dict]:

        pass

    def stop(self) -> None:
        pass
