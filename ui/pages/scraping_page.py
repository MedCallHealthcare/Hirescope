import threading
from queue import Queue
import pandas as pd
import requests
import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import datetime

from backend.runners.keyword_runner import KeywordRunner
from backend.pipeline import process_healthcare_jobs
from ui.pages.results_view import ResultsView


# Modern color palette
COLORS = {
    "bg_primary": "#f8f9fa",
    "bg_secondary": "#ffffff",
    "bg_dark": "#1a1d29",
    "text_primary": "#1e293b",
    "text_secondary": "#64748b",
    "text_light": "#94a3b8",
    "accent_primary": "#2563eb",
    "accent_hover": "#1d4ed8",
    "border": "#e2e8f0",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
}


class ModernCard(ctk.CTkFrame):
    """Reusable modern card component"""
    def __init__(self, parent, title=None, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS["bg_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )
        
        if title:
            self.title_label = ctk.CTkLabel(
                self,
                text=title,
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=COLORS["text_primary"],
                anchor="w"
            )
            self.title_label.pack(anchor="w", padx=20, pady=(20, 10))


class ModernButton(ctk.CTkButton):
    """Reusable modern button component"""
    def __init__(self, parent, is_primary=True, **kwargs):
        colors = {
            "fg_color": COLORS["accent_primary"] if is_primary else COLORS["bg_secondary"],
            "hover_color": COLORS["accent_hover"] if is_primary else COLORS["border"],
            "text_color": "#ffffff" if is_primary else COLORS["text_primary"],
            "border_width": 0 if is_primary else 1,
            "border_color": COLORS["border"],
        }
        
        super().__init__(
            parent,
            corner_radius=8,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            **colors,
            **kwargs
        )


class ScrapingPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_primary"])

        # Runtime state
        self.queue: Queue[str] = Queue()
        self.runner: KeywordRunner | None = None
        self.worker_thread: threading.Thread | None = None
        self.processing_thread: threading.Thread | None = None

        # Raw scraped jobs collected during the session
        self.session_jobs: list[dict] = []

        # Processed pipeline results
        self.processed_jobs: list[dict] = []
        self.facility_df = None
        self.pipeline_stats: dict = {}
        self.sharepoint_export_result: dict = {}

        self.total_keywords = 0
        self.current_keyword_index = 0
        self.current_keyword_jobs = 0
        self.total_scraped = 0
        
        self.showing_results = False

        self.run_active = False
        self.processing_active = False

        self._build_ui()
        self._poll_queue()

    def _build_ui(self):
        """Build the main UI with configuration and results views"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Container for switching between config and results
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Build both views
        self._build_config_view()
        self._build_results_view()
        
        # Show config view by default
        self.show_config_view()

    def _build_config_view(self):
        """Build the search configuration view"""
        self.config_view = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.config_view.grid_columnconfigure(0, weight=1)
        self.config_view.grid_columnconfigure(1, weight=1)
        self.config_view.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self.config_view, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=32, pady=(32, 24))
        
        ctk.CTkLabel(
            header,
            text="Search Configuration",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(side="left")

        # Left column - Configuration cards (scrollable)
        left_col = ctk.CTkScrollableFrame(
            self.config_view, 
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["text_secondary"]
        )
        left_col.grid(row=1, column=0, sticky="nsew", padx=(32, 12), pady=(0, 32))
        
        # Scraping Mode Card
        mode_card = ModernCard(left_col, title="Scraping Mode")
        mode_card.pack(fill="x", pady=(0, 16))
        
        mode_container = ctk.CTkFrame(mode_card, fg_color="transparent")
        mode_container.pack(fill="x", padx=20, pady=(0, 20))
        
        # self.scrape_mode = ctk.StringVar(value="auto")
        self.scrape_mode = ctk.StringVar(value="manual")
        
        # Mode buttons
        mode_buttons = ctk.CTkFrame(mode_container, fg_color="transparent")
        mode_buttons.pack(fill="x")
        mode_buttons.grid_columnconfigure(0, weight=1)
        mode_buttons.grid_columnconfigure(1, weight=1)
        
        self.auto_btn = ctk.CTkButton(
            mode_buttons,
            text="Auto",
            command=lambda: self._set_mode("auto"),
            corner_radius=8,
            height=44,
            fg_color=COLORS["accent_primary"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.auto_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        # Disable Auto
        self.auto_btn.configure(state="disabled")
        
        self.manual_btn = ctk.CTkButton(
            mode_buttons,
            text="Manual",
            command=lambda: self._set_mode("manual"),
            corner_radius=8,
            height=44,
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.manual_btn.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        
        
        # Manual page selector (hidden by default)
        self.manual_page_frame = ctk.CTkFrame(mode_container, fg_color="transparent")
        
        ctk.CTkLabel(
            self.manual_page_frame,
            text="Page Number",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(anchor="w", pady=(16, 8))
        
        # Page control container
        page_control = ctk.CTkFrame(self.manual_page_frame, fg_color="transparent")
        page_control.pack(fill="x")
        
        # Decrease button
        self.page_decrease_btn = ctk.CTkButton(
            page_control,
            text="−",
            width=50,
            height=44,
            command=self._decrease_page,
            corner_radius=8,
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.page_decrease_btn.pack(side="left", padx=(0, 8))
        
        # Page number display
        self.page_number_var = ctk.StringVar(value="1")
        self.page_number_label = ctk.CTkLabel(
            page_control,
            textvariable=self.page_number_var,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text_primary"],
            width=80,
            height=44,
            fg_color=COLORS["bg_secondary"],
            corner_radius=8
        )
        self.page_number_label.pack(side="left", padx=8)
        
        # Increase button
        self.page_increase_btn = ctk.CTkButton(
            page_control,
            text="+",
            width=50,
            height=44,
            command=self._increase_page,
            corner_radius=8,
            fg_color=COLORS["accent_primary"],
            hover_color=COLORS["accent_hover"],
            text_color="#ffffff",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.page_increase_btn.pack(side="left", padx=(8, 0))
        
        # Page info
        ctk.CTkLabel(
            self.manual_page_frame,
            text="Each page contains approximately 5-15 job listings",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            anchor="w"
        ).pack(anchor="w", pady=(8, 0))

        self._set_mode("manual")

        # Target Website Card
        website_card = ModernCard(left_col, title="Target Website")
        website_card.pack(fill="x", pady=(0, 16))
        
        self.source_menu = ctk.CTkOptionMenu(
            website_card,
            values=[
                "All Websites",
                "HealthJobsNationwide",
                "Indeed",
                "ZipRecruiter",
                "NurseRecruiter",
            ],
            height=44,
            corner_radius=8,
            fg_color=COLORS["text_primary"],
            button_color=COLORS["accent_primary"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_secondary"],
            font=ctk.CTkFont(size=14)
        )
        self.source_menu.set("All Websites")
        self.source_menu.pack(fill="x", padx=20, pady=(0, 20))

        # Search Filters Card
        filters_card = ModernCard(left_col, title="Search Filters")
        filters_card.pack(fill="x", pady=(0, 16))
        
        # Location
        ctk.CTkLabel(
            filters_card,
            text="LOCATION",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text_secondary"],
            anchor="w"
        ).pack(anchor="w", padx=20, pady=(10, 6))
        
        self.location_entry = ctk.CTkEntry(
            filters_card,
            placeholder_text="City, State, or Zip",
            height=44,
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["bg_secondary"],
            font=ctk.CTkFont(size=14)
        )
        self.location_entry.pack(fill="x", padx=20, pady=(0, 16))
        
        # Within Miles
        ctk.CTkLabel(
            filters_card,
            text="WITHIN MILES",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text_secondary"],
            anchor="w"
        ).pack(anchor="w", padx=20, pady=(0, 6))
        
        self.miles_menu = ctk.CTkOptionMenu(
            filters_card,
            values=[
                "Exact location only", 
                "Within 5 miles", 
                "Within 10 miles", 
                "Within 15 miles", 
                "Within 25 miles", 
                "Within 35 miles", 
                "Within 50 miles", 
                "Within 100 miles"
            ],
            height=44,
            corner_radius=8,
            fg_color=COLORS["text_primary"],
            button_color=COLORS["accent_primary"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_secondary"],
            font=ctk.CTkFont(size=14)
        )
        self.miles_menu.set("Within 25 miles")
        self.miles_menu.pack(fill="x", padx=20, pady=(0, 20))

        # Date posted
        ctk.CTkLabel(
            filters_card,
            text="DATE POSTED",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text_secondary"],
            anchor="w"
        ).pack(anchor="w", padx=20, pady=(0, 6))

        self.date_posted_map = {
            "All Dates": 0,
            "Jobs you haven't seen": "last",
            "Last 24 hours": 1,
            "Last 3 days": 3,
            "Last 7 days": 7,
            "Last 14 days": 14,
        }

        self.date_posted_menu = ctk.CTkOptionMenu(
            filters_card,
            values=list(self.date_posted_map.keys()),
            height=44,
            corner_radius=8,
            fg_color=COLORS["text_primary"],
            button_color=COLORS["accent_primary"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_secondary"],
            font=ctk.CTkFont(size=14)
        )
        self.date_posted_menu.set("All Dates")
        self.date_posted_menu.pack(fill="x", padx=20, pady=(0, 20))

                

        # Right column - Keywords and Logs
        right_col = ctk.CTkFrame(self.config_view, fg_color="transparent")
        right_col.grid(row=1, column=1, sticky="nsew", padx=(12, 32), pady=(0, 32))
        
        ## Keywords Row (Input + Positive)
        keywords_row = ctk.CTkFrame(right_col, fg_color="transparent")
        keywords_row.pack(fill="x", pady=(0, 16))

        keywords_row.grid_columnconfigure(0, weight=1)
        keywords_row.grid_columnconfigure(1, weight=1)

        # Input Keywords Card
        keywords_card = ModernCard(
            keywords_row,
            title="Job Search Terms"
        )
        keywords_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            keywords_card,
            text="Enter job titles or roles to search across selected job boards (one per line)",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(0, 8))

        self.keywords_text = ctk.CTkTextbox(
            keywords_card,
            height=150,
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["bg_secondary"],
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"]
        )
        self.keywords_text.pack(fill="x", padx=20, pady=(0, 20))

        self.keywords_text.insert(
            "1.0",
            "Registered Nurse\n"
            "Licensed Practical Nurse\n"
            "Certified Nursing Assistant\n"
            "Long Term Care RN\n"
            "Long Term Care LPN\n"
            "Long Term Care CNA\n"
            "LTC Nurse\n"
            "Nursing Home RN\n"
            "Nursing Home LPN\n"
            "Nursing Home CNA\n"
            "Skilled Nursing Facility RN\n"
            "Skilled Nursing Facility LPN\n"
            "Skilled Nursing Facility CNA\n"
            "Hospice RN\n"
            "Hospice LPN\n"
            "Veterans Home RN\n"
            "Veterans Home LPN"
        )

        # Positive Keywords Card (moved here from second row)
        positive_card = ModernCard(
            keywords_row,
            title="Include Keywords (Filter Results)"
        )
        positive_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        
        ctk.CTkLabel(
            positive_card,
            text="Only keep results that contain these words in the job title (or role) or company name.",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(0, 8))
        
        self.positive_keywords_text = ctk.CTkTextbox(
            positive_card,
            height=150,
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["bg_secondary"],
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"]
        )
        self.positive_keywords_text.pack(fill="x", padx=20, pady=(0, 20))
        
        self.positive_keywords_text.insert(
            "1.0",
            "e.g."
        )

        ## Keywords Row 2 (Negative Keywords)
        keywords_row2 = ctk.CTkFrame(right_col, fg_color="transparent")
        keywords_row2.pack(fill="x", pady=(0, 16))

        # Negative Keywords Card
        negative_card = ModernCard(
            keywords_row2,
            title="Exclude Keywords (Filter Results)"
        )
        negative_card.pack(fill="x")

        ctk.CTkLabel(
            negative_card,
            text="Remove results whose company name contains any of these words.",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(0, 8))

        self.negative_keywords_text = ctk.CTkTextbox(
            negative_card,
            height=120,
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["bg_secondary"],
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"]
        )
        self.negative_keywords_text.pack(fill="x", padx=20, pady=(0, 20))

        self.negative_keywords_text.insert(
            "1.0",
            "e.g.\nStaffing Agency\nRecruitment\nTemp Agency"
        )

        # Scrape Logs Card
        logs_card = ModernCard(right_col, title="SCRAPE LOGS")
        logs_card.pack(fill="both", expand=True, pady=(0, 0))
        
        # Statistics row above logs
        stats_container = ctk.CTkFrame(logs_card, fg_color="transparent")
        stats_container.pack(fill="x", padx=20, pady=(0, 12))
        stats_container.grid_columnconfigure(0, weight=1)
        stats_container.grid_columnconfigure(1, weight=1)
        stats_container.grid_columnconfigure(2, weight=1)
        stats_container.grid_columnconfigure(3, weight=1)
        
        # Create stat variables
        self.total_scraped_var = ctk.StringVar(value="0")
        self.total_keywords_var = ctk.StringVar(value="0")
        self.current_keyword_var = ctk.StringVar(value="-")
        self.remaining_keywords_var = ctk.StringVar(value="0")
        
        # Stat box helper function
        def create_stat_box(parent, label_text, value_var, column):
            stat_box = ctk.CTkFrame(
                parent,
                fg_color=COLORS["bg_primary"],
                corner_radius=8,
                border_width=1,
                border_color=COLORS["border"]
            )
            stat_box.grid(row=0, column=column, sticky="ew", padx=4)
            
            ctk.CTkLabel(
                stat_box,
                text=label_text,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=COLORS["text_secondary"]
            ).pack(pady=(8, 2))
            
            ctk.CTkLabel(
                stat_box,
                textvariable=value_var,
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color=COLORS["accent_primary"]
            ).pack(pady=(0, 8))
            
            return stat_box
        
        # Create stat boxes
        create_stat_box(stats_container, "TOTAL SCRAPED", self.total_scraped_var, 0)
        create_stat_box(stats_container, "TOTAL KEYWORDS", self.total_keywords_var, 1)
        create_stat_box(stats_container, "CURRENT KEYWORD", self.current_keyword_var, 2)
        create_stat_box(stats_container, "REMAINING KEYWORDS", self.remaining_keywords_var, 3)
        
        # Logs textbox with increased minimum height
        self.logs_text = ctk.CTkTextbox(
            logs_card,
            corner_radius=8,
            fg_color=COLORS["bg_dark"],
            text_color="#e5e7eb",
            font=ctk.CTkFont(family="Courier", size=12),
            height=400  # Set minimum height for better visibility
        )
        self.logs_text.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self._log("// Waiting for search initialization...")
        self._log("[SYSTEM] HireScope Data Tools initialized.")
        self._log("[SYSTEM] Ready for target selection.")
        
        # Status bar
        status_bar = ctk.CTkFrame(logs_card, fg_color="transparent", height=30)
        status_bar.pack(fill="x", padx=20, pady=(0, 16))
        
        ctk.CTkLabel(
            status_bar,
            text="STATUS: IDLE",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_light"]
        ).pack(side="left")
        
        self.cpu_label = ctk.CTkLabel(
            status_bar,
            text="CPU: 0.2%",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_light"]
        )
        self.cpu_label.pack(side="right")

        # Bottom action bar
        action_bar = ctk.CTkFrame(self.config_view, fg_color="transparent", height=80)
        action_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=32, pady=(0, 32))
        
        # Left side - Reset button
        self.reset_btn = ModernButton(
            action_bar,
            text="🔄 Reset All",
            command=self.reset_all,
            is_primary=False,
            width=140
        )
        self.reset_btn.pack(side="left")
        
        # Right side - Action buttons
        self.view_results_btn = ModernButton(
            action_bar,
            text="📊 View Results",
            command=self.show_results_view,
            is_primary=False,
            width=160,
            state="disabled"
        )
        self.view_results_btn.pack(side="right", padx=(12, 0))
        
        self.start_btn = ModernButton(
            action_bar,
            text="Start Scraping Process  →",
            command=self.start,
            width=240
        )
        self.start_btn.pack(side="right")
        
        self.stop_btn = ModernButton(
            action_bar,
            text="Stop Process",
            command=self.stop,
            is_primary=False,
            width=160,
            state="disabled"
        )
        self.stop_btn.pack(side="right", padx=(0, 12))

    def _build_results_view(self):
        self.results_view = ResultsView(
            parent=self.main_container,
            colors=COLORS,
            on_back=self.show_config_view,
            on_export=self.download_csv
        )


    def _set_mode(self, mode):
        """Update scraping mode and button states"""
        self.scrape_mode.set(mode)
        if mode == "auto":
            self.auto_btn.configure(
                fg_color=COLORS["accent_primary"],
                text_color="#ffffff",
                border_width=0
            )
            self.manual_btn.configure(
                fg_color=COLORS["bg_secondary"],
                text_color=COLORS["text_primary"],
                border_width=1,
                border_color=COLORS["border"]
            )
            # Hide manual page controls
            self.manual_page_frame.pack_forget()
        else:
            self.manual_btn.configure(
                fg_color=COLORS["accent_primary"],
                text_color="#ffffff",
                border_width=0
            )
            self.auto_btn.configure(
                fg_color=COLORS["bg_secondary"],
                text_color=COLORS["text_primary"],
                border_width=1,
                border_color=COLORS["border"]
            )
            # Show manual page controls
            self.manual_page_frame.pack(fill="x", pady=(8, 0))
    
    def _increase_page(self):
        """Increase the page number"""
        current = int(self.page_number_var.get())
        self.page_number_var.set(str(current + 1))
    
    def _decrease_page(self):
        """Decrease the page number (minimum 1)"""
        current = int(self.page_number_var.get())
        if current > 1:
            self.page_number_var.set(str(current - 1))
    
    def reset_all(self):
        """Reset all data and interface to initial state."""

        from tkinter import messagebox

        if self.run_active:
            messagebox.showwarning(
                "Scraping Active",
                "Stop the scraper and wait for it to finish before resetting."
            )
            return

        if self.processing_active:
            messagebox.showwarning(
                "Processing Active",
                "Please wait for processing and SharePoint export to finish before resetting."
            )
            return

        # Confirm reset
        if self.session_jobs:
            confirm = messagebox.askyesno(
                "Confirm Reset",
                "This will clear all scraped data and reset the interface. Continue?"
            )

            if not confirm:
                return
        
        # Stop any running scraper
        if self.runner:
            self.runner.stop()
            self.runner = None

        self.worker_thread = None
        self.processing_thread = None

        self.run_active = False
        self.processing_active = False
        
        # Clear all data
        self.session_jobs.clear()
        self.processed_jobs.clear()

        self.facility_df = None
        self.pipeline_stats = {}
        self.sharepoint_export_result = {}

        self.total_scraped = 0
        self.total_keywords = 0
        self.current_keyword_index = 0
        self.current_keyword_jobs = 0
        
        # Reset statistics display
        self.total_scraped_var.set("0")
        self.total_keywords_var.set("0")
        self.current_keyword_var.set("-")
        self.remaining_keywords_var.set("0")
        
        # Reset inputs
        # Reset job search terms
        self.keywords_text.delete("1.0", "end")
        self.keywords_text.insert(
            "1.0",
            "Registered Nurse\n"
            "Licensed Practical Nurse\n"
            "Certified Nursing Assistant\n"
            "Long Term Care RN\n"
            "Long Term Care LPN\n"
            "Long Term Care CNA\n"
            "LTC Nurse\n"
            "Nursing Home RN\n"
            "Nursing Home LPN\n"
            "Nursing Home CNA\n"
            "Skilled Nursing Facility RN\n"
            "Skilled Nursing Facility LPN\n"
            "Skilled Nursing Facility CNA\n"
            "Hospice RN\n"
            "Hospice LPN\n"
            "Veterans Home RN\n"
            "Veterans Home LPN"
        )

        # Reset positive keywords
        self.positive_keywords_text.delete("1.0", "end")
        self.positive_keywords_text.insert(
            "1.0",
            "e.g.\nAdvocate Health\nNorthwestern Medicine\nAscension Health"
        )

        # Reset negative keywords
        self.negative_keywords_text.delete("1.0", "end")
        self.negative_keywords_text.insert(
            "1.0",
            "e.g.\nStaffing Agency\nRecruitment\nTemp Agency"
        )
        self.location_entry.delete(0, "end")
        self.source_menu.set("All Websites")
        self.miles_menu.set("Within 25 miles")
        
        # # Reset to auto mode
        # self._set_mode("auto")
        # Reset to manual mode
        self._set_mode("manual")
        self.page_number_var.set("1")
        
        # Clear logs
        self.logs_text.delete("1.0", "end")
        self._log("// Waiting for search initialization...")
        self._log("[SYSTEM] HireScope Data Tools initialized.")
        self._log("[SYSTEM] Ready for target selection.")
        self._log("[INFO] All data has been reset.")
        
        # Disable View Results button
        self.view_results_btn.configure(state="disabled")
        
        # Enable Start button
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        
        self._log("[SUCCESS] Interface reset complete")

    def show_config_view(self):
        """Show the configuration view"""
        self.results_view.grid_remove()
        self.config_view.grid(row=0, column=0, sticky="nsew")
        self.showing_results = False

    def _get_filter_keywords(self):
        """
        Read positive and negative filter keywords from the UI.
        """

        positive_keywords = [
            line.strip().lower()
            for line in self.positive_keywords_text
            .get("1.0", "end")
            .splitlines()
            if line.strip()
            and not line.strip().lower().startswith("e.g.")
        ]

        negative_keywords = [
            line.strip().lower()
            for line in self.negative_keywords_text
            .get("1.0", "end")
            .splitlines()
            if line.strip()
            and not line.strip().lower().startswith("e.g.")
        ]

        return positive_keywords, negative_keywords

    def _run_processing_pipeline(
        self,
        jobs,
        positive_keywords,
        negative_keywords,
    ):
        """
        Run the healthcare processing pipeline in a background thread.
        """

        try:
            self.queue.put(
                "[PIPELINE] Starting healthcare processing pipeline..."
            )

            results = process_healthcare_jobs(
                jobs=jobs,
                positive_keywords=positive_keywords,
                negative_keywords=negative_keywords,
            )

            self.processed_jobs = results["jobs"]
            self.facility_df = results["facility_df"]
            self.pipeline_stats = results["stats"]

            self.sharepoint_export_result = results.get(
                "sharepoint_export",
                {}
            )

            stats = self.pipeline_stats

            self.queue.put(
                f"[PIPELINE] Final jobs: "
                f"{stats.get('final_jobs', 0)}"
            )

            self.queue.put(
                f"[PIPELINE] Blank rows removed: "
                f"{stats.get('blanks_removed', 0)}"
            )

            self.queue.put(
                f"[PIPELINE] Positive removed: "
                f"{stats.get('positive_removed', 0)}"
            )

            self.queue.put(
                f"[PIPELINE] Negative removed: "
                f"{stats.get('negative_removed', 0)}"
            )

            self.queue.put(
                f"[PIPELINE] Duplicates removed: "
                f"{stats.get('duplicates_removed', 0)}"
            )

            sharepoint = self.sharepoint_export_result

            self.queue.put("")
            self.queue.put("[SHAREPOINT] Export result:")

            self.queue.put(
                f"[SHAREPOINT] Added: "
                f"{sharepoint.get('added', 0)}"
            )

            self.queue.put(
                f"[SHAREPOINT] Existing duplicates: "
                f"{sharepoint.get('duplicates', 0)}"
            )

            self.queue.put(
                f"[SHAREPOINT] Errors: "
                f"{sharepoint.get('errors', 0)}"
            )

            self.queue.put(
                f"[SHAREPOINT] Attempts: "
                f"{sharepoint.get('attempts', 0)}"
            )

            self.queue.put(
                f"[SHAREPOINT] Status: "
                f"{sharepoint.get('status', 'unknown')}"
            )

            message = sharepoint.get("message")

            if message:
                self.queue.put(
                    f"[SHAREPOINT] {message}"
                )

            self.queue.put("[PIPELINE_COMPLETE]")

        except Exception as error:
            self.queue.put(
                f"[PIPELINE_ERROR] "
                f"{type(error).__name__}: {error}"
            )

    def show_results_view(self):
        """
        Display the already processed pipeline results.

        The pipeline automatically runs after scraping finishes,
        so clicking View Results must not run it again.
        """

        if self.processing_active:
            messagebox.showinfo(
                "Processing",
                "The scraped jobs are still being processed."
            )
            return

        if not self.processed_jobs:
            messagebox.showinfo(
                "No Results",
                "No processed job data is available."
            )
            return

        self.config_view.grid_remove()

        self.results_view.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.showing_results = True

        self.results_view.update_results(
            jobs=self.processed_jobs,
            facility_df=self.facility_df,
            duplicates_removed=self.pipeline_stats.get(
                "duplicates_removed",
                0
            ),
            positive_keywords_filtered=self.pipeline_stats.get(
                "positive_removed",
                0
            )
        )



    def _populate_results(self):
        """Populate the results table with scraped jobs"""
        # Clear existing results
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        # Update subtitle
        count = len(self.session_jobs)
        self.results_subtitle.configure(
            text=f"Found {count} matching healthcare position{'s' if count != 1 else ''}"
        )

        # Add job rows
        for i, job in enumerate(self.session_jobs):
            self._add_result_row(i, job)

    def _truncate(self, text, max_len=35):
        if not text:
            return "N/A"
        return text if len(text) <= max_len else text[:max_len - 3] + "..."

    def _add_result_row(self, index, job):
        row = ctk.CTkFrame(self.results_scroll, fg_color="transparent", height=60)
        row.grid(row=index, column=0, sticky="ew", pady=1)

        for i in range(5):
            row.grid_columnconfigure(i, weight=1)

        values = [
            self._truncate(job.get("job_title")),
            self._truncate(job.get("company_name")),
            self._truncate(job.get("location")),
            job.get("source", "N/A").upper(),
            job.get("scraped_at", "N/A"),
        ]

        for col, value in enumerate(values):
            ctk.CTkLabel(
                row,
                text=value,
                anchor="w",
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text_primary"],
            ).grid(row=0, column=col, sticky="w", padx=12)


    def start(self):
        """Start the scraping process"""

        if self.run_active or self.processing_active:
            messagebox.showinfo(
                "Process Running",
                "A scraping or processing operation is already running."
            )
            return

        keywords = [
            line.strip()
            for line in self.keywords_text.get("1.0", "end").splitlines()
            if line.strip() and not line.startswith("e.g.")
        ]

        location = self.location_entry.get().strip()

        if not keywords or not location:
            self._log(
                "[ERROR] Keywords and location are required"
            )

            messagebox.showerror(
                "Error",
                "Please enter keywords and location"
            )
            return

        # Clear results from the previous processing run
        # only after the new scrape has passed validation.
        # Raw session_jobs are intentionally preserved.
        self.processed_jobs.clear()
        self.facility_df = None
        self.pipeline_stats = {}
        self.sharepoint_export_result = {}

        self.view_results_btn.configure(
            state="disabled"
        )

        # UI radius -> Indeed radius
        radius_map = {
            "Exact location only": 0,
            "Within 5 miles": 5,
            "Within 10 miles": 10,
            "Within 15 miles": 15,
            "Within 25 miles": 25,
            "Within 35 miles": 35,
            "Within 50 miles": 50,
            "Within 100 miles": 100,
        }
        radius = radius_map.get(self.miles_menu.get(), 25)

        fromage = self.date_posted_map.get(
            self.date_posted_menu.get(), 0
        )

        self._log(f"[INFO] Date Posted filter: {self.date_posted_menu.get()} (fromage={fromage})")

        source_map = {
            "All Websites": "any",
            "HealthJobsNationwide": "healthjobsnationwide",
            "Indeed": "indeed",
            "ZipRecruiter": "ziprecruiter",
            "NurseRecruiter": "nurserecruiter",
        }
        selected_source = source_map.get(self.source_menu.get(), "any")

        scrape_mode = self.scrape_mode.get()
        manual_start = None

        if scrape_mode == "manual":
            page_number = int(self.page_number_var.get())
            manual_start = (page_number - 1) * 10
            self._log(f"[INFO] Manual mode: Page {page_number} (offset {manual_start})")

        self._log(f"[INFO] Location: {location}")
        self._log(f"[INFO] Radius: {radius} miles")
        self._log(f"[INFO] Date Posted: {fromage} days")
        self._log(f"[INFO] Source: {selected_source}")

        self.run_active = True

        self.runner = KeywordRunner(
            keywords=keywords,
            location=location,
            radius=radius,
            fromage=fromage, 
            selected_source=selected_source,
            scrape_mode=scrape_mode,
            start_offset=manual_start,
            log_callback=self.queue.put,
        )

        self.worker_thread = threading.Thread(target=self.runner.run, daemon=True)
        self.worker_thread.start()

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

    def stop(self):
        """
        Request the active scraper to stop.

        Start remains disabled until the worker thread
        has actually finished.
        """

        if self.runner:
            self.runner.stop()

        self._log(
            "[INFO] Stop requested. Finishing current operation..."
        )

        self.stop_btn.configure(
            state="disabled"
        )

        self.start_btn.configure(
            state="disabled"
        )

    def download_csv(self):
        """Download processed job data as CSV with auto filename."""

        if not self.processed_jobs:
            messagebox.showwarning(
                "No Data",
                "No processed data available to export."
            )
            return

        timestamp = datetime.now().strftime(
            "%m-%d-%Y_%I-%M-%S_%p"
        )

        default_name = (
            f"processed_jobs_{timestamp}.csv"
        )

        path = filedialog.asksaveasfilename(
            initialfile=default_name,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if path:
            try:
                pd.DataFrame(
                    self.processed_jobs
                ).to_csv(
                    path,
                    index=False
                )

                messagebox.showinfo(
                    "Success",
                    f"Data exported to:\n{path}"
                )

            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Failed to export data:\n{str(e)}"
                )


    def send_to_make(self):
        """Send data to Make.com webhook"""
        url = self.webhook_entry.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please enter a webhook URL")
            return

        payload = {"jobs": self.session_jobs}
        try:
            requests.post(url, json=payload, timeout=30)
            messagebox.showinfo("Success", "Data sent to Make.com")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send data: {str(e)}")

    def _poll_queue(self):
        """
        Poll the queue for scraper and pipeline messages
        and update the UI.
        """

        while not self.queue.empty():
            msg = self.queue.get()

            if msg.startswith("[KEYWORD_START]"):
                _, payload = msg.split("]", 1)

                index, total, keyword = (
                    payload.strip().split("|")
                )

                self.current_keyword_index = int(index)
                self.total_keywords = int(total)

                self.total_keywords_var.set(total)
                self.current_keyword_var.set(keyword)

                self.remaining_keywords_var.set(
                    str(int(total) - int(index))
                )

                self._log(msg)

            elif msg.startswith("[KEYWORD_DONE]"):
                _, payload = msg.split("]", 1)

                index, jobs_count = (
                    payload.strip().split("|")
                )

                jobs_count = int(jobs_count)

                self.total_scraped += jobs_count

                self.total_scraped_var.set(
                    str(self.total_scraped)
                )

                self._log(msg)

            elif msg == "[PIPELINE_COMPLETE]":
                self.processing_active = False
                self.processing_thread = None

                self.start_btn.configure(
                    state="normal"
                )

                sharepoint_status = (
                    self.sharepoint_export_result.get(
                        "status",
                        "unknown"
                    )
                )

                self._log("")

                if sharepoint_status in (
                    "success",
                    "no_changes",
                    "no_data",
                ):
                    self._log(
                        "[SUCCESS] Automatic processing completed."
                    )

                else:
                    self._log(
                        "[WARN] Processing completed, but the "
                        "SharePoint export needs attention."
                    )

                if self.processed_jobs:
                    self.view_results_btn.configure(
                        state="normal"
                    )

                    self._log(
                        "[INFO] Click 'View Results' to review "
                        "the processed jobs."
                    )

                else:
                    self.view_results_btn.configure(
                        state="disabled"
                    )

                    self._log(
                        "[INFO] Processing completed, but no "
                        "jobs remained after filtering."
                    )

            elif msg.startswith("[PIPELINE_ERROR]"):
                self.processing_active = False
                self.processing_thread = None

                self.start_btn.configure(
                    state="normal"
                )

                self.view_results_btn.configure(
                    state="disabled"
                )

                error_message = msg.replace(
                    "[PIPELINE_ERROR]",
                    ""
                ).strip()

                self._log(
                    f"[ERROR] Pipeline failed: {error_message}"
                )

                messagebox.showerror(
                    "Processing Error",
                    error_message
                )

            else:
                self._log(msg)

        # ==========================================
        # SCRAPING THREAD COMPLETED
        # ==========================================

        if (
            self.run_active
            and self.worker_thread
            and not self.worker_thread.is_alive()
        ):
            # Prevent this completion block from
            # running repeatedly every 200ms.
            self.run_active = False
            self.worker_thread = None

            self.stop_btn.configure(
                state="disabled"
            )

            finished_runner = self.runner

            # ==========================================
            # SCRAPE WAS MANUALLY STOPPED
            # ==========================================

            if (
                finished_runner
                and finished_runner.stop_requested
            ):
                stopped_jobs = list(
                    finished_runner.all_jobs
                )

                finished_runner.all_jobs.clear()

                if stopped_jobs:
                    self.session_jobs.extend(
                        stopped_jobs
                    )

                self._log("")
                self._log(
                    "[STOPPED] Scraping process was stopped."
                )

                self._log(
                    f"[STOPPED] Partial jobs collected: "
                    f"{len(stopped_jobs)}"
                )

                self._log(
                    "[INFO] Partial jobs were not processed "
                    "or exported to SharePoint."
                )

                self.start_btn.configure(
                    state="normal"
                )

                self.view_results_btn.configure(
                    state="disabled"
                )

            # ==========================================
            # SCRAPE COMPLETED NORMALLY
            # ==========================================

            elif (
                finished_runner
                and finished_runner.all_jobs
            ):
                scraped_jobs = list(
                    finished_runner.all_jobs
                )

                finished_runner.all_jobs.clear()

                self.session_jobs.extend(
                    scraped_jobs
                )

                self._log("")
                self._log(
                    f"[COMPLETE] Scraping finished. "
                    f"Jobs collected: {len(scraped_jobs)}"
                )

                self._log(
                    "[INFO] Starting automatic processing..."
                )

                positive_keywords, negative_keywords = (
                    self._get_filter_keywords()
                )

                self.processing_active = True

                self.start_btn.configure(
                    state="disabled"
                )

                self.view_results_btn.configure(
                    state="disabled"
                )

                self.processing_thread = threading.Thread(
                    target=self._run_processing_pipeline,
                    args=(
                        scraped_jobs,
                        positive_keywords,
                        negative_keywords,
                    ),
                    daemon=True,
                )

                self.processing_thread.start()

            else:
                self._log(
                    "[INFO] Scraping finished with no jobs."
                )

                self.start_btn.configure(
                    state="normal"
                )

            self.runner = None

        self.after(
            200,
            self._poll_queue
        )

    def _log(self, msg):
        """Add message to log console"""
        self.logs_text.insert("end", msg + "\n")
        self.logs_text.see("end")