import customtkinter as ctk
from ui.widgets.job_table import JobTable
from collections import Counter
from tkinter import filedialog
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
from pathlib import Path
from datetime import datetime
from tkinter import ttk
import requests
import threading
from tkinter import messagebox, simpledialog
from backend.export.export_excel import export_excel_report
from backend.export.sharepoint_excel_exporter import (
    export_jobs_to_sharepoint
)

class AnalyticsCard(ctk.CTkFrame):
    """A card widget to display a single statistic"""
    
    def __init__(self, parent, title: str, value: str, icon: str = "📊", color: str = "#e3f2fd"):
        super().__init__(parent, fg_color=color, corner_radius=12)
        
        # Icon
        icon_label = ctk.CTkLabel(
            self, 
            text=icon, 
            font=("Arial", 32),
            text_color="#1a1a1a"
        )
        icon_label.pack(pady=(16, 8))
        
        # Value
        value_label = ctk.CTkLabel(
            self, 
            text=value, 
            font=("Arial Bold", 28),
            text_color="#1a1a1a"
        )
        value_label.pack(pady=4)
        
        # Title
        title_label = ctk.CTkLabel(
            self, 
            text=title, 
            font=("Arial", 12),
            text_color="#424242"
        )
        title_label.pack(pady=(0, 16))


class MatplotlibChart(ctk.CTkFrame):
    """A matplotlib-based chart widget that can be embedded in tkinter"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#ffffff", corner_radius=12, **kwargs)
        self.figure = None
        self.canvas = None
        self.view_all_callback = None
    
    def create_bar_chart(self, data: dict, title: str, max_bars: int = 10, color: str = "#2563eb", view_all_callback=None):
        """Create a horizontal bar chart using matplotlib"""
        # Clear any existing chart
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        if self.figure:
            plt.close(self.figure)
        
        # Clear any existing view all button
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                widget.destroy()
        
        if not data:
            no_data_label = ctk.CTkLabel(
                self,
                text="No data available",
                font=("Arial", 12),
                text_color="#757575"
            )
            no_data_label.pack(pady=50)
            return
        
        # Sort data in DESCENDING order (highest first) and limit
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:max_bars]
        
        # REVERSE the sorted data so highest appears at TOP when plotted
        sorted_data = list(reversed(sorted_data))
        
        labels = [item[0] for item in sorted_data]
        values = [item[1] for item in sorted_data]
        
        # Truncate long labels
        labels = [label if len(label) <= 30 else label[:27] + "..." for label in labels]
        
        # Create figure
        bar_count = len(labels)
        self.figure = plt.Figure(
            figsize=(6, max(4, bar_count * 0.45)),  # dynamic height
            dpi=100,
            facecolor='white'
        )
        ax = self.figure.add_subplot(111)
        
        y_positions = range(len(labels))

        # Create horizontal bar chart
        bars = ax.barh(y_positions, values, color=color, alpha=0.85)
        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels)
        
        # Customize appearance
        ax.set_xlabel('Number of Jobs', fontsize=10, fontweight='bold')
        ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='x', alpha=0.3, linestyle='--')

        self.figure.subplots_adjust(left=0.35)
        
        # Add value labels on bars
        for bar in bars:
            width = bar.get_width()
            y = bar.get_y() + bar.get_height() / 2

            ax.text(
                width + max(values) * 0.02,  # more padding
                y,
                f"{int(width)}",
                va="center",
                fontsize=9,
                fontweight="bold",
                clip_on=False
            )


        
        # Adjust layout
        self.figure.tight_layout()
        
        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(10, 5))
        
        # Add "View All ..." button if there's more data than displayed
        if len(data) > max_bars and view_all_callback:
            self.view_all_callback = view_all_callback
            view_all_btn = ctk.CTkButton(
                self,
                text=f"View All {title.split()[1]}",  # Extract category name (e.g., "Job Titles", "Companies")
                command=view_all_callback,
                height=28,
                font=("Arial", 11),
                fg_color="#2563eb",
                hover_color="#1d4ed8",
                corner_radius=6
            )
            view_all_btn.pack(pady=(0, 10), padx=10)
    
    def get_figure(self):
        """Return the matplotlib figure for export"""
        return self.figure


class ResultsView(ctk.CTkFrame):
    def __init__(self, parent, colors, on_back, on_export):
        super().__init__(parent, fg_color="transparent")

        self.COLORS = colors
        self.on_back = on_back
        self.on_export = on_export
        self.jobs_data = []
        self.facility_df = pd.DataFrame()
        self.duplicates_removed = 0
        self.positive_keywords_filtered = 0
        self.stats = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_ui()

    def _build_ui(self):
        # Header with buttons
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=32, pady=24)

        ctk.CTkButton(
            header, 
            text="←", 
            command=self.on_back,
            width=40,
            height=40,
            font=ctk.CTkFont(size=18)
        ).pack(side="left")
        
        # Add toggle analytics button
        self.analytics_visible = True
        self.toggle_analytics_btn = ctk.CTkButton(
            header, 
            text="📊 Hide Analytics", 
            command=self._toggle_analytics
        )
        self.toggle_analytics_btn.pack(side="left", padx=16)
        
        # Export dropdown menu
        export_frame = ctk.CTkFrame(header, fg_color="transparent")
        export_frame.pack(side="right")
        
        # Create export menu variable
        self.export_option = ctk.StringVar(value="Select format")
        
        # Export menu
        self.export_menu = ctk.CTkOptionMenu(
            export_frame,
            variable=self.export_option,
            values=[
                "CSV",
                "Excel (.xlsx)",
                "SharePoint Excel",
                "ZIP",
                "Make.com"
            ],
            command=self._handle_export_selection,
            width=200,
            height=40,
            fg_color="#2563eb",
            button_color="#1d4ed8",
            button_hover_color="#1e40af",
            dropdown_fg_color="#ffffff",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.export_menu.pack(side="left")
        
        # Export button
        ctk.CTkButton(
            export_frame,
            text="📥 Export Data",
            command=self._trigger_export,
            width=140,
            height=40,
            fg_color="#10b981",
            hover_color="#059669",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(8, 0))

        # Analytics section
        self.analytics_container = ctk.CTkFrame(self, fg_color="transparent")
        self.analytics_container.grid(row=1, column=0, sticky="ew", padx=32, pady=(0, 16))
        self.analytics_container.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        self.stat_cards = []
        self._create_analytics_section()

        # Table container
        table_container = ctk.CTkFrame(self)
        table_container.grid(row=2, column=0, sticky="nsew", padx=32, pady=(0, 32))
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(0, weight=1)

        self.table = JobTable(table_container)

    def _create_analytics_section(self):
        """Create the analytics cards section"""
        # Statistics cards row
        stats_frame = ctk.CTkFrame(self.analytics_container, fg_color="transparent")
        stats_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 16))
        stats_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        
        # Placeholder cards - 6 cards without negative keywords
        card_configs = [
            ("Total Jobs", "0", "💼", "#e3f2fd"),
            ("Companies", "0", "🏢", "#e8f5e9"),
            ("Keywords", "0", "🔑", "#f3e5f5"),
            ("Duplicates Removed", "0", "🗑️", "#ffebee"),
            ("Positive Keywords", "0", "✅", "#e8f5e9"),
            ("Job Demand", "0", "📊", "#fff3e0"),
        ]
        
        for idx, (title, value, icon, color) in enumerate(card_configs):
            card = AnalyticsCard(stats_frame, title, value, icon, color)
            card.grid(row=0, column=idx, sticky="ew", padx=4)
            self.stat_cards.append(card)
        
        # Job Summary heading
        summary_heading = ctk.CTkLabel(
            self.analytics_container,
            text="Job Summary",
            font=("Arial Bold", 20),
            text_color="#1a1a1a"
        )
        summary_heading.grid(row=1, column=0, columnspan=4, sticky="w", pady=(16, 8))
        
        # Charts row - 2 charts (Companies and Job Demand)
        charts_frame = ctk.CTkFrame(self.analytics_container, fg_color="transparent")
        charts_frame.grid(row=2, column=0, columnspan=4, sticky="ew")
        charts_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Companies Chart (Blue)
        self.company_chart = MatplotlibChart(charts_frame)
        self.company_chart.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        
        # Job Demand Chart (Orange) - replaces Location chart
        self.job_demand_chart = MatplotlibChart(charts_frame)
        self.job_demand_chart.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    def _toggle_analytics(self):
        """Toggle analytics section visibility"""
        if self.analytics_visible:
            self.analytics_container.grid_remove()
            self.toggle_analytics_btn.configure(text="📊 Show Analytics")
        else:
            self.analytics_container.grid()
            self.toggle_analytics_btn.configure(text="📊 Hide Analytics")
        self.analytics_visible = not self.analytics_visible

    def _analyze_jobs(self, jobs: list[dict]):
        """Analyze job data and return statistics"""
        if not jobs:
            return {
                "total": 0,
                "companies": 0,
                "keywords": 0,
                "job_titles": 0,
                "companies_data": {},
                "job_titles_data": {},
            }
        
        companies = [job.get("company_name", "Unknown") for job in jobs]
        keywords = [job.get("search_keyword", "Unknown") for job in jobs]
        job_titles = [job.get("job_title", "Unknown") for job in jobs]
        
        companies_count = Counter(companies)
        job_titles_count = Counter(job_titles)
        
        return {
            "total": len(jobs),
            "companies": len(set(companies)),
            "keywords": len(set(keywords)),
            "job_titles": len(set(job_titles)),
            "companies_data": dict(companies_count),
            "job_titles_data": dict(job_titles_count),
        }

    def _show_all_data(self, title: str, data: dict):
        popup = ctk.CTkToplevel(self)
        popup.title(f"All {title}")
        popup.geometry("800x600")

        header_label = ctk.CTkLabel(
            popup,
            text=f"All {title}",
            font=("Arial Bold", 20)
        )
        header_label.pack(pady=16)

        container = ctk.CTkFrame(popup)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        # Treeview
        tree = ttk.Treeview(
            container,
            columns=("name", "count"),
            show="headings",
            height=20
        )

        tree.heading("name", text=title[:-1])   # Company / Job Title
        tree.heading("count", text="Jobs")

        tree.column("name", anchor="w", width=450)
        tree.column("count", anchor="center", width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=tree.yview
        )
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Insert sorted data
        for idx, (name, count) in enumerate(
            sorted(data.items(), key=lambda x: x[1], reverse=True), 1
        ):
            tree.insert("", "end", values=(name, count))

    def _update_analytics(self, jobs: list[dict]):
        """Update analytics cards and charts with job data"""
        self.stats = self._analyze_jobs(jobs)
        
        # Clear existing cards
        for card in self.stat_cards:
            card.destroy()
        self.stat_cards.clear()
        
        # Recreate stats cards with updated data
        stats_frame = ctk.CTkFrame(self.analytics_container, fg_color="transparent")
        stats_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 16))
        stats_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        
        card_configs = [
            ("Total Jobs", str(self.stats["total"]), "💼", "#e3f2fd"),
            ("Companies", str(self.stats["companies"]), "🏢", "#e8f5e9"),
            ("Keywords", str(self.stats["keywords"]), "🔑", "#f3e5f5"),
            ("Duplicates Removed", str(self.duplicates_removed), "🗑️", "#ffebee"),
            ("Positive Keywords", str(self.positive_keywords_filtered), "✅", "#e8f5e9"),
            ("Job Demand", str(self.stats["job_titles"]), "📊", "#fff3e0"),
        ]
        
        for idx, (title, value, icon, color) in enumerate(card_configs):
            card = AnalyticsCard(stats_frame, title, value, icon, color)
            card.grid(row=0, column=idx, sticky="ew", padx=4)
            self.stat_cards.append(card)
        
        # Update matplotlib charts with "View All" buttons
        self.company_chart.create_bar_chart(
            self.stats["companies_data"],
            "Top Companies",
            max_bars=10,
            color="#2563eb",  # Blue
            view_all_callback=lambda: self._show_all_data("Companies", self.stats["companies_data"])
        )
        
        # Job Demand Chart - shows top job titles
        self.job_demand_chart.create_bar_chart(
            self.stats["job_titles_data"],
            "Job Demand (Top Titles)",
            max_bars=10,
            color="#f59e0b",  # Orange
            view_all_callback=lambda: self._show_all_data("Job Titles", self.stats["job_titles_data"])
        )

    def update_results(
        self,
        jobs: list[dict],
        facility_df=None,
        duplicates_removed: int = 0,
        positive_keywords_filtered: int = 0
    ):
        """Update both table and analytics with job data"""
        self.jobs_data = jobs
        self.facility_df = facility_df if facility_df is not None else pd.DataFrame()
        self.duplicates_removed = duplicates_removed
        self.positive_keywords_filtered = positive_keywords_filtered

        self.table.insert_jobs(jobs)
        self._update_analytics(jobs)

    def _create_analytics_image(self):
        """Create dashboard-style analytics image using matplotlib"""

        from matplotlib.gridspec import GridSpec

        # Create large figure
        fig = plt.figure(figsize=(16, 10), dpi=150)
        fig.patch.set_facecolor("#f8f9fa")

        gs = GridSpec(3, 2, height_ratios=[0.8, 2, 2], figure=fig)

        # ===== TITLE =====
        fig.text(
            0.05, 0.95,
            "Job Analysis Report",
            fontsize=22,
            fontweight="bold",
            color="#1e293b"
        )

        fig.text(
            0.05, 0.92,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            fontsize=10,
            color="#64748b"
        )

        # ===== METRICS SECTION =====
        metrics = [
            ("Total Jobs", self.stats['total']),
            ("Companies", self.stats['companies']),
            ("Keywords", self.stats['keywords']),
            ("Job Demand", self.stats['job_titles']),
            ("Duplicates Removed", self.duplicates_removed),
            ("Positive Keywords", self.positive_keywords_filtered),
        ]

        for i, (label, value) in enumerate(metrics):
            fig.text(
                0.05 + (i % 3) * 0.3,
                0.85 - (i // 3) * 0.05,
                f"{label}: {value}",
                fontsize=12,
                color="#111827"
            )

        # ===== TOP COMPANIES CHART =====
        ax1 = fig.add_subplot(gs[1, 0])
        companies = sorted(
            self.stats["companies_data"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        if companies:
            labels, values = zip(*companies)
            ax1.barh(labels[::-1], values[::-1], color="#2563eb")
            ax1.set_title("Top Companies", fontweight="bold")
            ax1.set_xlabel("Number of Jobs")

        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)

        # ===== JOB DEMAND CHART =====
        ax2 = fig.add_subplot(gs[1, 1])
        titles = sorted(
            self.stats["job_titles_data"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        if titles:
            labels, values = zip(*titles)
            ax2.barh(labels[::-1], values[::-1], color="#f59e0b")
            ax2.set_title("Job Demand (Top Titles)", fontweight="bold")
            ax2.set_xlabel("Number of Jobs")

        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)

        # plt.tight_layout(rect=[0, 0, 1, 0.9])
        fig.tight_layout(rect=[0, 0, 1, 0.9])

        return fig


    def _handle_export_selection(self, choice):
        """Store the export choice but don't execute until Export button is clicked"""
        pass  # Just store the selection in self.export_option

    def _trigger_export(self):
        """Execute the export based on the selected option"""
        choice = self.export_option.get()

        if choice == "Select format":
            messagebox.showwarning(
                "No Format Selected",
                "Please select an export format first."
            )
            return

        if choice == "CSV":
            self._export_csv()

        elif choice == "Excel (.xlsx)":
            self._export_excel()

        elif choice == "SharePoint Excel":
            self._export_sharepoint()

        elif choice == "ZIP":
            self._export_zip()

        elif choice == "Make.com":
            self._export_make()

    def _export_csv(self):
        """Export processed results to CSV only when user clicks Export."""
        if not self.jobs_data:
            messagebox.showwarning(
                "No Data",
                "No results available to export."
            )
            return

        now = datetime.now()
        default_filename = now.strftime("healthcare_jobs_%m-%d-%Y_%I_%M_%p.csv")

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_filename,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export CSV Results"
        )

        if not file_path:
            return

        try:
            df = pd.DataFrame(self.jobs_data)

            df.to_csv(
                file_path,
                index=False,
                encoding="utf-8-sig"
            )

            messagebox.showinfo(
                "Export Successful",
                f"CSV file exported successfully:\n\n{file_path}"
            )

            print("✅ Successfully exported CSV file!")
            print(f"   Location: {file_path}")
            print(f"   Total jobs: {len(self.jobs_data)}")

        except Exception as e:
            messagebox.showerror(
                "Export Error",
                f"Failed to export CSV file:\n\n{str(e)}"
            )

            print(f"❌ CSV export error: {e}")

    def _export_excel(self):
        """Export processed healthcare report to Excel only when user clicks Export."""
        if not self.jobs_data:
            messagebox.showwarning(
                "No Data",
                "No results available to export."
            )
            return

        now = datetime.now()
        default_filename = now.strftime("healthcare_report_%m-%d-%Y_%I_%M_%p.xlsx")

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=default_filename,
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Export Excel Report"
        )

        if not file_path:
            return

        try:
            export_path = export_excel_report(
                jobs=self.jobs_data,
                facility_df=self.facility_df,
                output_path=file_path
            )

            messagebox.showinfo(
                "Export Successful",
                f"Excel report exported successfully:\n\n{export_path}"
            )

            print("✅ Successfully exported Excel report!")
            print(f"   Location: {export_path}")
            print(f"   Total jobs: {len(self.jobs_data)}")

        except Exception as e:
            messagebox.showerror(
                "Export Error",
                f"Failed to export Excel report:\n\n{str(e)}"
            )

            print(f"❌ Export error: {e}")

    def _export_sharepoint(self):
        """
        Export the current processed jobs to the
        SharePoint-synced Excel workbook.
        """

        if not self.jobs_data:
            messagebox.showwarning(
                "No Data",
                "No processed results are available to export."
            )
            return

        confirm = messagebox.askyesno(
            "Export to SharePoint Excel",
            (
                f"Export {len(self.jobs_data)} processed jobs "
                "to the SharePoint Excel workbook?\n\n"
                "Existing duplicate jobs will be skipped."
            )
        )

        if not confirm:
            return

        def run_export():
            try:
                result = export_jobs_to_sharepoint(
                    self.jobs_data
                )

                def show_result():
                    status = result.get("status", "unknown")
                    added = result.get("added", 0)
                    duplicates = result.get("duplicates", 0)
                    errors = result.get("errors", 0)
                    attempts = result.get("attempts", 0)
                    message = result.get("message", "")

                    if status == "success":
                        messagebox.showinfo(
                            "SharePoint Export Successful",
                            (
                                "The Excel workbook was updated successfully.\n\n"
                                f"Added: {added}\n"
                                f"Duplicates skipped: {duplicates}\n"
                                f"Errors: {errors}\n"
                                f"Attempts: {attempts}\n\n"
                                "OneDrive will sync the saved workbook "
                                "to SharePoint automatically."
                            )
                        )

                    elif status == "no_changes":
                        messagebox.showinfo(
                            "No New Jobs",
                            (
                                "No new jobs were added.\n\n"
                                f"Duplicates skipped: {duplicates}\n"
                                f"Attempts: {attempts}\n\n"
                                "These jobs already exist in the workbook."
                            )
                        )

                    elif status == "no_data":
                        messagebox.showwarning(
                            "No Data",
                            message
                        )

                    else:
                        messagebox.showerror(
                            "SharePoint Export Failed",
                            (
                                f"Status: {status}\n"
                                f"Added: {added}\n"
                                f"Duplicates: {duplicates}\n"
                                f"Errors: {errors}\n"
                                f"Attempts: {attempts}\n\n"
                                f"{message}"
                            )
                        )

                self.after(
                    0,
                    show_result
                )

            except Exception as error:
                error_message = str(error)

                self.after(
                    0,
                    lambda: messagebox.showerror(
                        "SharePoint Export Error",
                        (
                            "An unexpected error occurred while "
                            "exporting to SharePoint Excel:\n\n"
                            f"{error_message}"
                        )
                    )
                )

        threading.Thread(
            target=run_export,
            daemon=True
        ).start()


    def _export_make(self):
        """Send data to Make.com webhook"""
        if not self.jobs_data:
            print("No data to export")
            return
        
        # Ask user for webhook URL
        webhook_url = simpledialog.askstring(
            "Make.com Webhook",
            "Enter your Make.com webhook URL:",
            parent=self
        )
        
        if not webhook_url or not webhook_url.strip():
            return
        
        try:
            payload = {"jobs": self.jobs_data}
            response = requests.post(webhook_url.strip(), json=payload, timeout=30)
            response.raise_for_status()
            
            print(f"✅ Successfully sent data to Make.com!")
            print(f"   Webhook: {webhook_url}")
            print(f"   Jobs sent: {len(self.jobs_data)}")
            print(f"   Response: {response.status_code}")
            
            messagebox.showinfo(
                "Success", 
                f"Data sent successfully to Make.com!\n\nJobs sent: {len(self.jobs_data)}\nResponse: {response.status_code}"
            )
        except requests.exceptions.Timeout:
            print(f"❌ Request timeout")
            messagebox.showerror("Error", "Request timed out. Please check your webhook URL and try again.")
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            messagebox.showerror("Error", f"Failed to send data to Make.com:\n{str(e)}")
        except Exception as e:
            print(f"❌ Error: {e}")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

    def _export_zip(self):
        """Export results as ZIP file containing CSV, Excel, analytics image, and summary text"""
        if not self.jobs_data:
            print("No data to export")
            return
        
        from openpyxl.utils import get_column_letter
        
        # Generate default filename with format: scrape_jobs_MM-DD-YYYY_HH_MM_AM/PM.zip
        now = datetime.now()
        default_filename = now.strftime("scrape_jobs_%m-%d-%Y_%I_%M_%p.zip")
        
        # Ask user where to save with default filename
        file_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            initialfile=default_filename,
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
            title="Export Analysis Results"
        )
        
        if not file_path:
            return
        
        try:
            # Create ZIP file
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add CSV file
                csv_buffer = io.StringIO()
                df = pd.DataFrame(self.jobs_data)
                df.to_csv(csv_buffer, index=False)
                zipf.writestr('job_data.csv', csv_buffer.getvalue())
                
                # Add Excel file with summary sheets
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    # Write main job data
                    df_jobs = pd.DataFrame(self.jobs_data)
                    df_jobs.to_excel(writer, sheet_name='Job Data', index=False)
                    
                    # Create combined summary sheet with proper structure
                    # Companies section
                    companies_data = []
                    for company, count in sorted(self.stats["companies_data"].items(), key=lambda x: x[1], reverse=True):
                        companies_data.append([company, count, '', ''])
                    
                    # Job Demand section
                    job_demand_data = []
                    for title, count in sorted(self.stats["job_titles_data"].items(), key=lambda x: x[1], reverse=True):
                        job_demand_data.append(['', '', title, count])
                    
                    # Combine both sections
                    max_rows = max(len(companies_data), len(job_demand_data))
                    summary_data = []
                    
                    for i in range(max_rows):
                        if i < len(companies_data) and i < len(job_demand_data):
                            # Both have data
                            summary_data.append(companies_data[i][:2] + job_demand_data[i][2:])
                        elif i < len(companies_data):
                            # Only companies have data
                            summary_data.append(companies_data[i])
                        else:
                            # Only job demand have data
                            summary_data.append(job_demand_data[i])
                    
                    # Create DataFrame with proper column names
                    df_summary = pd.DataFrame(summary_data, columns=['Company Name', '# of job listed', 'Job Title', 'Demand Count'])
                    df_summary.to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Create separate companies summary
                    companies_summary = []
                    for company, count in sorted(self.stats["companies_data"].items(), key=lambda x: x[1], reverse=True):
                        companies_summary.append({
                            'Company Name': company,
                            '# of job listed': count
                        })
                    
                    if companies_summary:
                        df_companies = pd.DataFrame(companies_summary)
                        df_companies.to_excel(writer, sheet_name='Companies Summary', index=False)
                    
                    # Create separate job demand summary
                    job_demand_summary = []
                    for title, count in sorted(self.stats["job_titles_data"].items(), key=lambda x: x[1], reverse=True):
                        job_demand_summary.append({
                            'Job Title': title,
                            'Demand Count': count
                        })
                    
                    if job_demand_summary:
                        df_job_demand = pd.DataFrame(job_demand_summary)
                        df_job_demand.to_excel(writer, sheet_name='Job Demand Summary', index=False)
                    
                    # Auto-adjust column widths for all sheets
                    workbook = writer.book
                    for sheet_name in workbook.sheetnames:
                        worksheet = workbook[sheet_name]
                        
                        for column_cells in worksheet.columns:
                            max_length = 0
                            column_letter = get_column_letter(column_cells[0].column)
                            
                            for cell in column_cells:
                                try:
                                    if cell.value:
                                        cell_length = len(str(cell.value))
                                        if cell_length > max_length:
                                            max_length = cell_length
                                except:
                                    pass
                            
                            # Set column width with some padding
                            adjusted_width = min(max_length + 2, 50)  # Max width of 50
                            worksheet.column_dimensions[column_letter].width = adjusted_width
                
                excel_buffer.seek(0)
                zipf.writestr('job_data.xlsx', excel_buffer.getvalue())
                
                # Add analytics image
                fig = self._create_analytics_image()

                img_buffer = io.BytesIO()
                fig.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
                plt.close(fig)  # VERY IMPORTANT

                zipf.writestr('analytics_report.png', img_buffer.getvalue())
                
                # Add summary text file
                summary = f"""Job Analysis Summary
===================
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Metrics:
--------
Total Jobs: {self.stats['total']}
Unique Companies: {self.stats['companies']}
Unique Keywords: {self.stats['keywords']}
Job Demand (Unique Titles): {self.stats['job_titles']}
Duplicates Removed: {self.duplicates_removed}
Positive Keywords Filtered: {self.positive_keywords_filtered}

All Companies:
-----------------
"""
                sorted_companies = sorted(self.stats["companies_data"].items(), key=lambda x: x[1], reverse=True)
                for company, count in sorted_companies:
                    summary += f"{company}: {count} jobs\n"
                
                summary += "\nJob Demand (All Titles):\n-----------------\n"
                sorted_titles = sorted(self.stats["job_titles_data"].items(), key=lambda x: x[1], reverse=True)
                for title, count in sorted_titles:
                    summary += f"{title}: {count} jobs\n"
                
                zipf.writestr('summary.txt', summary)
            
            # Success message to console
            print(f"✅ Successfully exported ZIP file!")
            print(f"   Location: {file_path}")
            print(f"   Contains: job_data.csv, job_data.xlsx, analytics_report.png, summary.txt")
            
        except Exception as e:
            print(f"❌ Export error: {e}")
            import traceback
            traceback.print_exc()