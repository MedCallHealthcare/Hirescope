import customtkinter as ctk
from tkinterdnd2 import TkinterDnD

from ui.sidebar import Sidebar
from ui.pages.scraping_page import ScrapingPage
from ui.pages.analysis_page import AnalysisPage

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class MedCallApp(TkinterDnD.Tk):
    def __init__(self):
        TkinterDnD.Tk.__init__(self)

        self.title("HireScope Tool – Job Scraper Control Panel")
        self.state("zoomed")
        # self.minsize(1200, 700)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = Sidebar(self, self.show_page)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        # Page container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # Pages
        self.pages = {
            "scrape": ScrapingPage(self.container),
            "analysis": AnalysisPage(self.container),
        }

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.show_page("scrape")

    def show_page(self, page_key: str):
        for page in self.pages.values():
            page.grid_remove()

        self.pages[page_key].grid()
        self.sidebar.set_active(page_key)
