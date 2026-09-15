import customtkinter as ctk
import threading
from queue import Queue

from backend.runners.keyword_runner import KeywordRunner
from backend.pipeline import process_healthcare_jobs

class ScrapingPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        # Runtime state
        self.queue: Queue[str] = Queue()
        self.runner: KeywordRunner | None = None
        self.worker_thread: threading.Thread | None = None

        self.session_jobs: list[dict] = []
        self.total_keywords = 0
        self.current_keyword_index = 0
        self.current_keyword_jobs = 0
        self.total_scraped = 0
        
        self.showing_results = False

        self.run_active = False

        print("test")

    def create_small_layout(self):
        self.frame.pack_forget()
        self.frame = ctk.Frame(self)

    