import customtkinter as ctk


# Modern color palette
SIDEBAR_BG = "#0f172b"
TEXT_COLOR = "#94a3b8"
ACTIVE_BG = "#2563eb"
ACTIVE_TEXT = "#ffffff"
HOVER_BG = "#1e293b"
BORDER_COLOR = "#1e293b"


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, navigate_callback):
        super().__init__(
            parent,
            width=240,
            corner_radius=0,
            fg_color=SIDEBAR_BG
        )

        self.navigate_callback = navigate_callback
        self.grid_propagate(False)

        # Logo/Title section
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(pady=(32, 0), padx=20)

        # Icon (you can replace with actual logo)
        icon_label = ctk.CTkLabel(
            title_frame,
            text="⚕️",
            font=ctk.CTkFont(size=32),
        )
        icon_label.pack()

        ctk.CTkLabel(
            title_frame,
            text="HireScope Tool",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#ffffff",
        ).pack()

        ctk.CTkLabel(
            title_frame,
            text="Data Tools",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_COLOR,
        ).pack()

        # Divider
        ctk.CTkFrame(
            self,
            height=1,
            fg_color=BORDER_COLOR
        ).pack(fill="x", pady=32, padx=20)

        # Navigation section
        nav_label = ctk.CTkLabel(
            self,
            text="NAVIGATION",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_COLOR,
            anchor="w"
        )
        nav_label.pack(anchor="w", padx=20, pady=(0, 12))

        self.buttons = {}

        self._add_nav("🔍 Scraping Tool", "scrape", "Search and collect job data")

        # Bottom section
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=20, pady=20)

        # Divider
        ctk.CTkFrame(
            bottom_frame,
            height=1,
            fg_color=BORDER_COLOR
        ).pack(fill="x", pady=(0, 20))


    def _add_nav(self, label, key, description=None):
        """Add a navigation button with optional description"""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=16, pady=4)

        btn = ctk.CTkButton(
            container,
            text=label,
            command=lambda: self.navigate_callback(key),
            fg_color="transparent",
            hover_color=HOVER_BG,
            text_color=TEXT_COLOR,
            anchor="w",
            corner_radius=8,
            height=44,
            font=ctk.CTkFont(size=14, weight="normal")
        )
        btn.pack(fill="x")
        
        if description:
            desc_label = ctk.CTkLabel(
                container,
                text=description,
                font=ctk.CTkFont(size=11),
                text_color=TEXT_COLOR,
                anchor="w"
            )
            desc_label.pack(anchor="w", padx=12, pady=(2, 0))

        self.buttons[key] = btn


    def set_active(self, active_key):
        """Set the active navigation item"""
        for key, btn in self.buttons.items():
            if key == active_key:
                btn.configure(
                    fg_color=ACTIVE_BG,
                    text_color=ACTIVE_TEXT,
                    font=ctk.CTkFont(size=14, weight="bold")
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=TEXT_COLOR,
                    font=ctk.CTkFont(size=14, weight="normal")
                )