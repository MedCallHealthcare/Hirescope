import tkinter as tk
from tkinter import ttk

class JobTable(ttk.Treeview):
    COLUMNS = (
        "job_title",
        "company",
        "location",
        "source",
        "scraped_at"
    )

    def __init__(self, parent):
        super().__init__(
            parent,
            columns=self.COLUMNS,
            show="headings",
            height=15
        )

        self._setup_columns()
        self._setup_scrollbar(parent)

    def _setup_columns(self):
        headings = {
            "job_title": "JOB TITLE",
            "company": "COMPANY",
            "location": "LOCATION",
            "source": "SOURCE",
            "scraped_at": "SCRAPED AT",
        }

        widths = {
            "job_title": 240,
            "company": 200,
            "location": 180,
            "source": 120,
            "scraped_at": 160,
        }

        for col in self.COLUMNS:
            self.heading(col, text=headings[col])
            self.column(col, width=widths[col], anchor="w")

    def _setup_scrollbar(self, parent):
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.yview)
        self.configure(yscrollcommand=scrollbar.set)

        self.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def clear(self):
        for row in self.get_children():
            self.delete(row)

    def insert_jobs(self, jobs: list[dict]):
        self.clear()

        for job in jobs:
            self.insert(
                "",
                "end",
                values=(
                    job.get("job_title", "N/A"),
                    job.get("company_name", "N/A"),
                    job.get("location", "N/A"),
                    job.get("source", "").upper(),
                    job.get("scraped_at", "N/A"),
                )
            )
