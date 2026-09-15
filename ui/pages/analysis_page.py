import customtkinter as ctk
from tkinter import filedialog
import pandas as pd
from pathlib import Path
import sys
import os
from tkinterdnd2 import DND_FILES

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.filter.deduplicate import deduplicate
from backend.filter.filter_positive_keywords import filter_positive_keywords
from backend.filter.filter_negative_keywords import filter_negative_keywords

import ftfy
import pandas as pd


COLORS = {
    "bg_primary": "#f8f9fa",
    "bg_secondary": "#ffffff",
    "text_primary": "#1e293b",
    "text_secondary": "#64748b",
    "border": "#e2e8f0",
    "accent_primary": "#2563eb",
    "accent_hover": "#1d4ed8",
    "success": "#10b981",
    "error": "#ef4444",
}


def normalize_text(value):
    if not isinstance(value, str) or pd.isna(value):
        return ""

    value = ftfy.fix_text(value)
    return " ".join(value.split())



class ModernCard(ctk.CTkFrame):
    """A modern card container with title"""
    
    def __init__(self, parent, title="", **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS["bg_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )
        
        if title:
            title_label = ctk.CTkLabel(
                self,
                text=title,
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=COLORS["text_primary"]
            )
            title_label.pack(anchor="w", padx=20, pady=(20, 12))


class DragDropZone(ctk.CTkFrame):
    """Drag and drop file upload zone using tkinterdnd2"""
    
    def __init__(self, parent, on_file_selected, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS["bg_secondary"],
            corner_radius=12,
            border_width=2,
            border_color=COLORS["border"],
            **kwargs
        )
        
        self.on_file_selected = on_file_selected
        self.file_path = None
        self._drag_active = False
        
        # Configure drag and drop using tkinterdnd2
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<DropEnter>>', self._on_drag_enter)
        self.dnd_bind('<<DropLeave>>', self._on_drag_leave)
        self.dnd_bind('<<Drop>>', self._on_drop)
        
        # Content container
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=40, pady=40)
        
        # Icon
        self.icon_label = ctk.CTkLabel(
            content,
            text="📁",
            font=ctk.CTkFont(size=64)
        )
        self.icon_label.pack(pady=(0, 16))
        
        # Main text
        self.main_text = ctk.CTkLabel(
            content,
            text="Drag & Drop CSV File Here",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.main_text.pack(pady=(0, 8))
        
        # Sub text
        self.sub_text = ctk.CTkLabel(
            content,
            text="or click to browse",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"]
        )
        self.sub_text.pack(pady=(0, 20))
        
        # Browse button
        self.browse_btn = ctk.CTkButton(
            content,
            text="Browse Files",
            command=self._browse_file,
            fg_color=COLORS["accent_primary"],
            hover_color=COLORS["accent_hover"],
            corner_radius=8,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.browse_btn.pack()
        
        # File info (hidden initially)
        self.file_info = ctk.CTkLabel(
            content,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["success"]
        )
        self.file_info.pack(pady=(16, 0))
        
        # Make frame clickable
        self.bind("<Button-1>", lambda e: self._browse_file())
    
    def _browse_file(self):
        """Open file browser dialog"""
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            self._set_file(file_path)
    
    def _on_drag_enter(self, event):
        """Handle drag enter event"""
        self._drag_active = True
        self.configure(border_color=COLORS["accent_primary"])
        self.configure(border_width=3)
        return event.action
    
    def _on_drag_leave(self, event):
        """Handle drag leave event"""
        self._drag_active = False
        self.configure(border_color=COLORS["border"])
        self.configure(border_width=2)
        return event.action
    
    def _on_drop(self, event):
        """Handle file drop event"""
        self._drag_active = False
        self.configure(border_color=COLORS["border"])
        self.configure(border_width=2)
        
        if event.data:
            # tkinterdnd2 returns paths in various formats depending on OS
            # On Windows: {C:/path/to/file.csv}
            # On Linux/Mac: /path/to/file.csv or {/path/to/file.csv}
            
            # Clean up the file path - remove braces and quotes
            file_path = event.data.strip()
            
            # Handle multiple files (take only the first one)
            if file_path.startswith('{'):
                # Remove outer braces
                file_path = file_path.strip('{}')
                # Split by } { in case of multiple files
                files = file_path.split('} {')
                file_path = files[0].strip()
            
            # Remove any remaining quotes
            file_path = file_path.strip('\'"')
            
            # Check if it's a CSV file
            if file_path.lower().endswith('.csv'):
                self._set_file(file_path)
            else:
                self._show_error("Please drop a CSV file")
    
    def _set_file(self, file_path):
        """Set the selected file and update UI"""
        self.file_path = file_path
        file_name = Path(file_path).name
        
        # Update UI to show file is selected
        self.icon_label.configure(text="✅")
        self.main_text.configure(text=file_name)
        self.sub_text.configure(text="File loaded successfully")
        self.file_info.configure(text=f"Path: {file_path}")
        
        # Notify parent
        if self.on_file_selected:
            self.on_file_selected(file_path)
    
    def _show_error(self, message):
        """Show error message temporarily"""
        self.icon_label.configure(text="❌")
        self.main_text.configure(text=message)
        self.sub_text.configure(text="Please try again")
        
        # Reset after 2 seconds
        self.after(2000, self._reset_to_drop_state)
    
    def _reset_to_drop_state(self):
        """Reset to the initial drop state if no file is selected"""
        if not self.file_path:
            self.icon_label.configure(text="📁")
            self.main_text.configure(text="Drag & Drop CSV File Here")
            self.sub_text.configure(text="or click to browse")
    
    def reset(self):
        """Reset the drop zone to initial state"""
        self.file_path = None
        self.icon_label.configure(text="📁")
        self.main_text.configure(text="Drag & Drop CSV File Here")
        self.sub_text.configure(text="or click to browse")
        self.file_info.configure(text="")
        self.configure(border_color=COLORS["border"])
        self.configure(border_width=2)



class AnalysisPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_primary"])
        
        self.csv_file_path = None
        self.jobs_data = []
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Import ResultsView here to avoid circular imports
        from ui.pages.results_view import ResultsView
        
        # Create container for both views
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        
        # Create the input form (scrollable)
        self.input_view = ctk.CTkScrollableFrame(
            self.container,
            fg_color="transparent"
        )
        self.input_view.grid(row=0, column=0, sticky="nsew")
        self.input_view.grid_columnconfigure(0, weight=1)
        
        # Create the results view (initially hidden)
        self.results_view = ResultsView(
            self.container,
            colors=COLORS,
            on_back=self._show_input_view,
            on_export=self._export_results
        )
        
        # Build the input UI
        self._build_input_ui()
        
        # Start with input view
        self.current_view = "input"
    
    def _build_input_ui(self):
        # Header
        header = ctk.CTkFrame(self.input_view, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=32, pady=(32, 24))
        
        ctk.CTkLabel(
            header,
            text="📊 CSV Data Analysis",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header,
            text="Import your CSV file, configure filters, and analyze your data",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", pady=(8, 0))
        
        # File Import Section
        import_card = ModernCard(
            self.input_view,
            title="1. Import CSV File"
        )
        import_card.grid(row=1, column=0, sticky="ew", padx=32, pady=(0, 16))
        
        self.drop_zone = DragDropZone(
            import_card,
            on_file_selected=self._on_file_selected,
            height=250
        )
        self.drop_zone.pack(fill="x", padx=20, pady=(0, 20))
        
        # File preview info
        self.file_preview = ctk.CTkLabel(
            import_card,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            justify="left"
        )
        self.file_preview.pack(anchor="w", padx=20, pady=(0, 20))
        
        # Positive Keywords Section
        positive_keywords_card = ModernCard(
            self.input_view,
            title="2. Configure Positive Keywords (Optional)"
        )
        positive_keywords_card.grid(row=2, column=0, sticky="ew", padx=32, pady=(0, 16))
        
        ctk.CTkLabel(
            positive_keywords_card,
            text="Enter keywords to include in job title or company name (one per line, case-insensitive)",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(0, 12))
        
        self.positive_keywords_text = ctk.CTkTextbox(
            positive_keywords_card,
            height=150,
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["bg_primary"],
            font=ctk.CTkFont(size=13),
        )
        self.positive_keywords_text.pack(fill="x", padx=20, pady=(0, 20))
        
        # Placeholder text for positive keywords
        positive_placeholder = "e.g.\nAdvocate Health\nNorthwestern Medicine\nAscension Health"
        self.positive_keywords_text.insert("1.0", positive_placeholder)
        self.positive_keywords_text.bind("<FocusIn>", self._clear_positive_placeholder)
        self._is_positive_placeholder = True
        
        # Negative Keywords Section
        negative_keywords_card = ModernCard(
            self.input_view,
            title="3. Configure Negative Keywords (Optional)"
        )
        negative_keywords_card.grid(row=3, column=0, sticky="ew", padx=32, pady=(0, 16))

        ctk.CTkLabel(
            negative_keywords_card,
            text="Enter keywords to exclude — removes any job whose company name contains these words (one per line, case-insensitive)",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self.negative_keywords_text = ctk.CTkTextbox(
            negative_keywords_card,
            height=150,
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["bg_primary"],
            font=ctk.CTkFont(size=13),
        )
        self.negative_keywords_text.pack(fill="x", padx=20, pady=(0, 20))

        # Placeholder text for negative keywords
        negative_placeholder = "e.g.\nStaffing Agency\nRecruitment\nTemp Agency"
        self.negative_keywords_text.insert("1.0", negative_placeholder)
        self.negative_keywords_text.bind("<FocusIn>", self._clear_negative_placeholder)
        self._is_negative_placeholder = True

        # Analysis Options Section
        options_card = ModernCard(
            self.input_view,
            title="4. Analysis Options"
        )
        options_card.grid(row=4, column=0, sticky="ew", padx=32, pady=(0, 16))
        
        # Processing pipeline info
        pipeline_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        pipeline_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            pipeline_frame,
            text="Processing Pipeline:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 12))
        
        # Checkbox variables
        self.filter_positive_var = ctk.BooleanVar(value=True)
        self.filter_negative_var = ctk.BooleanVar(value=True)
        self.remove_duplicates_var = ctk.BooleanVar(value=True)
        self.sort_results_var = ctk.BooleanVar(value=True)
        
        # Checkbox options
        checkbox_frame = ctk.CTkFrame(pipeline_frame, fg_color="transparent")
        checkbox_frame.pack(fill="x", anchor="w")
        
        # Filter positive keywords checkbox
        self.filter_positive_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="Filter positive keywords in job title or company name",
            variable=self.filter_positive_var,
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_primary"],
            fg_color=COLORS["accent_primary"],
            hover_color=COLORS["accent_hover"],
            command=self._on_positive_filter_checkbox_changed
        )
        self.filter_positive_checkbox.pack(anchor="w", pady=6)
        
        # Info label about positive keywords
        self.positive_keywords_info = ctk.CTkLabel(
            checkbox_frame,
            text="💡 Enable positive keyword filtering to use keywords from Section 2",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        self.positive_keywords_info.pack(anchor="w", padx=25, pady=(4, 0))

        # Filter negative keywords checkbox
        self.filter_negative_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="Filter negative keywords in company name",
            variable=self.filter_negative_var,
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_primary"],
            fg_color=COLORS["accent_primary"],
            hover_color=COLORS["accent_hover"],
            command=self._on_negative_filter_checkbox_changed
        )
        self.filter_negative_checkbox.pack(anchor="w", pady=6)

        # Info label about negative keywords
        self.negative_keywords_info = ctk.CTkLabel(
            checkbox_frame,
            text="💡 Enable negative keyword filtering to use keywords from Section 3",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        self.negative_keywords_info.pack(anchor="w", padx=25, pady=(4, 0))
        
        # Remove duplicates checkbox
        self.remove_duplicates_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="Remove duplicate entries (same title, company, location)",
            variable=self.remove_duplicates_var,
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_primary"],
            fg_color=COLORS["accent_primary"],
            hover_color=COLORS["accent_hover"]
        )
        self.remove_duplicates_checkbox.pack(anchor="w", pady=6)
        
        # Sort results checkbox
        self.sort_results_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="Sort results alphabetically by job title",
            variable=self.sort_results_var,
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_primary"],
            fg_color=COLORS["accent_primary"],
            hover_color=COLORS["accent_hover"]
        )
        self.sort_results_checkbox.pack(anchor="w", pady=6)
        
        # Action Buttons
        action_frame = ctk.CTkFrame(self.input_view, fg_color="transparent")
        action_frame.grid(row=6, column=0, sticky="ew", padx=32, pady=(0, 32))
        
        self.analyze_btn = ctk.CTkButton(
            action_frame,
            text="🚀 Start Analysis",
            command=self._start_analysis,
            fg_color=COLORS["accent_primary"],
            hover_color=COLORS["accent_hover"],
            corner_radius=8,
            height=48,
            font=ctk.CTkFont(size=16, weight="bold"),
            state="disabled"
        )
        self.analyze_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        self.reset_btn = ctk.CTkButton(
            action_frame,
            text="🔄 Reset",
            command=self._reset_form,
            fg_color="transparent",
            hover_color=COLORS["border"],
            border_width=2,
            border_color=COLORS["border"],
            corner_radius=8,
            height=48,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.reset_btn.pack(side="left", padx=(8, 0))
        
        # Status message
        self.status_label = ctk.CTkLabel(
            self.input_view,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        )
        self.status_label.grid(row=7, column=0, sticky="ew", padx=32, pady=(0, 32))
    
    def _clear_positive_placeholder(self, event):
        """Clear positive keywords placeholder text on focus"""
        if self._is_positive_placeholder:
            self.positive_keywords_text.delete("1.0", "end")
            self._is_positive_placeholder = False

    def _clear_negative_placeholder(self, event):
        """Clear negative keywords placeholder text on focus"""
        if self._is_negative_placeholder:
            self.negative_keywords_text.delete("1.0", "end")
            self._is_negative_placeholder = False

    def _on_positive_filter_checkbox_changed(self):
        """Handle filter positive keywords checkbox change"""
        if self.filter_positive_var.get():
            # Show info label when enabled
            self.positive_keywords_info.pack(anchor="w", padx=25, pady=(4, 0))
        else:
            # Hide info label when disabled
            self.positive_keywords_info.pack_forget()

    def _on_negative_filter_checkbox_changed(self):
        """Handle filter negative keywords checkbox change"""
        if self.filter_negative_var.get():
            self.negative_keywords_info.pack(anchor="w", padx=25, pady=(4, 0))
        else:
            self.negative_keywords_info.pack_forget()

    def _get_negative_keywords(self):
        """Get negative keywords from text box"""
        if self._is_negative_placeholder:
            return []

        text = self.negative_keywords_text.get("1.0", "end").strip()
        if not text:
            return []

        return [line.strip() for line in text.split("\n") if line.strip()]
    
    def _on_file_selected(self, file_path):
        """Handle file selection"""
        self.csv_file_path = file_path
        
        try:
            # Load CSV to get preview info
            df = pd.read_csv(file_path)
            rows, cols = df.shape
            
            preview_text = f"✓ Loaded: {rows:,} rows × {cols} columns\n"
            preview_text += f"Columns: {', '.join(df.columns.tolist()[:5])}"
            if len(df.columns) > 5:
                preview_text += f" ... (+{len(df.columns) - 5} more)"
            
            self.file_preview.configure(text=preview_text)
            self.analyze_btn.configure(state="normal")
            self._update_status("File loaded successfully. Ready to analyze.", COLORS["success"])
            
        except Exception as e:
            self.file_preview.configure(text=f"❌ Error loading file: {str(e)}")
            self.analyze_btn.configure(state="disabled")
            self._update_status(f"Error: {str(e)}", COLORS["error"])
    
    def _get_positive_keywords(self):
        """Get positive keywords from text box"""
        if self._is_positive_placeholder:
            return []

        text = self.positive_keywords_text.get("1.0", "end").strip()
        if not text:
            return []

        return [line.strip() for line in text.split("\n") if line.strip()]

    
    def _start_analysis(self):
        """Start the analysis pipeline and show results"""
        if not self.csv_file_path:
            self._update_status("Please select a CSV file first.", COLORS["error"])
            return
        
        self._update_status("🔄 Processing...", COLORS["accent_primary"])
        self.analyze_btn.configure(state="disabled")
        
        try:
            # Load CSV
            df = pd.read_csv(self.csv_file_path)
            jobs = df.to_dict('records')

            for job in jobs:
                for key in ("company_name", "job_title", "location"):
                    if key in job:
                        job[key] = normalize_text(job[key])
            
            initial_count = len(jobs)
            self._update_status(f"📊 Loaded {initial_count:,} jobs from CSV...", COLORS["text_secondary"])
            
            # DEBUG: Print checkbox states
            print(f"\n{'='*60}")
            print(f"DEBUG: Analysis Options")
            print(f"{'='*60}")
            print(f"Filter Positive Keywords: {self.filter_positive_var.get()}")
            print(f"Filter Negative Keywords: {self.filter_negative_var.get()}")
            print(f"Remove Duplicates: {self.remove_duplicates_var.get()}")
            print(f"Sort Results: {self.sort_results_var.get()}")
            
            # Initialize counters
            positive_removed = 0
            negative_removed = 0
            duplicates_removed = 0
            
            # Step 1: Filter positive keywords (if enabled)
            if self.filter_positive_var.get():
                positive_keywords = self._get_positive_keywords()
                print(f"Positive Keywords ({len(positive_keywords)}): {positive_keywords}")
                
                if positive_keywords:
                    jobs, positive_removed = filter_positive_keywords(jobs, positive_keywords)
                    self._update_status(
                        f"✓ Filtered {positive_removed:,} jobs not matching positive keywords...",
                        COLORS["text_secondary"]
                    )
                else:
                    self._update_status(
                        "⊘ Skipped positive keyword filtering (no keywords provided)...",
                        COLORS["text_secondary"]
                    )
            else:
                self._update_status(
                    "⊘ Skipped positive keyword filtering (disabled)...",
                    COLORS["text_secondary"]
                )

            # Step 2: Filter negative keywords (if enabled)
            negative_removed = 0
            if self.filter_negative_var.get():
                negative_keywords = self._get_negative_keywords()
                print(f"Negative Keywords ({len(negative_keywords)}): {negative_keywords}")

                if negative_keywords:
                    jobs, negative_removed = filter_negative_keywords(jobs, negative_keywords)
                    self._update_status(
                        f"✓ Filtered {negative_removed:,} jobs matching negative keywords...",
                        COLORS["text_secondary"]
                    )
                else:
                    self._update_status(
                        "⊘ Skipped negative keyword filtering (no keywords provided)...",
                        COLORS["text_secondary"]
                    )
            else:
                self._update_status(
                    "⊘ Skipped negative keyword filtering (disabled)...",
                    COLORS["text_secondary"]
                )

            # Step 3: Deduplicate (if enabled)
            if self.remove_duplicates_var.get():
                jobs, duplicates_removed = deduplicate(jobs)
                self._update_status(
                    f"✓ Removed {duplicates_removed:,} duplicate jobs...",
                    COLORS["text_secondary"]
                )
            else:
                self._update_status(
                    "⊘ Skipped duplicate removal (disabled)...",
                    COLORS["text_secondary"]
                )
            
            # Step 4: Sort by job title (if enabled)
            if self.sort_results_var.get():
                jobs.sort(key=lambda x: x.get('job_title', '').lower())
                self._update_status(
                    "✓ Sorted results alphabetically...",
                    COLORS["text_secondary"]
                )
            else:
                self._update_status(
                    "⊘ Skipped sorting (disabled)...",
                    COLORS["text_secondary"]
                )
            
            final_count = len(jobs)
            
            # Store results
            self.jobs_data = jobs
            
            # Success message
            self._update_status(
                f"✅ Analysis complete! {final_count:,} jobs remaining "
                f"({initial_count - final_count:,} filtered out)",
                COLORS["success"]
            )
            
            # Show results view
            self._show_results_view(jobs, duplicates_removed, positive_removed)
            
        except Exception as e:
            self._update_status(f"❌ Error: {str(e)}", COLORS["error"])
            print(f"Analysis error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.analyze_btn.configure(state="normal")
    
    def _show_results_view(self, jobs, duplicates_removed, positive_removed):
        """Switch from input view to results view"""
        # Hide input view
        self.input_view.grid_remove()
        
        # Update and show results view
        self.results_view.update_results(
            jobs, 
            duplicates_removed, 
            positive_removed
        )
        self.results_view.grid(row=0, column=0, sticky="nsew")
        
        self.current_view = "results"
    
    def _show_input_view(self):
        """Switch from results view back to input view"""
        # Hide results view
        self.results_view.grid_remove()
        
        # Show input view
        self.input_view.grid(row=0, column=0, sticky="nsew")
        
        self.current_view = "input"
    
    def _export_results(self):
        """Export results to CSV"""
        if not self.jobs_data:
            return
        
        # Generate default filename with format: scrape_jobs_MM-DD-YYYY_HH_MM_AM/PM.csv
        from datetime import datetime
        now = datetime.now()
        default_filename = now.strftime("scrape_jobs_%m-%d-%Y_%I_%M_%p.csv")
        
        # Ask user where to save with default filename
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_filename,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Filtered Results"
        )
        
        if file_path:
            try:
                # Convert to DataFrame and save
                df = pd.DataFrame(self.jobs_data)
                df.to_csv(file_path, index=False)
                
                # Show success message
                print(f"✅ Successfully exported CSV file!")
                print(f"   Location: {file_path}")
                print(f"   Total jobs: {len(self.jobs_data)}")
                
            except Exception as e:
                print(f"❌ Export error: {e}")
    
    def _reset_form(self):
        """Reset the form to initial state"""
        self.drop_zone.reset()
        self.csv_file_path = None
        self.jobs_data = []
        self.file_preview.configure(text="")
        
        # Reset positive keywords
        self.positive_keywords_text.delete("1.0", "end")
        positive_placeholder = "e.g.\nAdvocate Health\nNorthwestern Medicine\nAscension Health"
        self.positive_keywords_text.insert("1.0", positive_placeholder)
        self._is_positive_placeholder = True

        # Reset negative keywords
        self.negative_keywords_text.delete("1.0", "end")
        negative_placeholder = "e.g.\nStaffing Agency\nRecruitment\nTemp Agency"
        self.negative_keywords_text.insert("1.0", negative_placeholder)
        self._is_negative_placeholder = True
        
        self.analyze_btn.configure(state="disabled")
        self._update_status("", "")
    
    def _update_status(self, message, color):
        """Update status label"""
        self.status_label.configure(text=message, text_color=color)
        self.update_idletasks()