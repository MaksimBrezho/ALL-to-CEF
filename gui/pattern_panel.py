import tkinter as tk
from tkinter import ttk
from utils.color_utils import get_shaded_color

class PatternPanel(tk.Frame):
    def __init__(self, master=None, patterns=None, on_toggle_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.patterns = patterns or []
        self.on_toggle_callback = on_toggle_callback
        self.check_vars = {}
        self.checkboxes = {}

        self.canvas = tk.Canvas(self, borderwidth=0, width=kwargs.get("width", 140))
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.frame = ttk.Frame(self.canvas)

        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh(self, color_map=None, pattern_index_map=None):
        for widget in self.frame.winfo_children():
            widget.destroy()

        category_colors = color_map or {}
        self.check_vars.clear()
        self.checkboxes.clear()

        sorted_patterns = sorted(self.patterns, key=lambda p: (p.get("category", ""), p.get("name", "")))
        current_category = None

        for pat in sorted_patterns:
            category = pat.get("category", "")
            if category != current_category:
                current_category = category
                header = ttk.Label(self.frame, text=f"— {category} —", font=("Segoe UI", 9, "bold"))
                header.pack(anchor="w", pady=(5, 1), padx=(2, 2))

            row = ttk.Frame(self.frame)
            row.pack(fill="x", padx=2, pady=1)

            key = (pat.get("category"), pat.get("regex"))
            idx = pattern_index_map.get(key, 0) if pattern_index_map else 0
            base = category_colors.get(pat.get("category"), "#000")
            shade = get_shaded_color(base, idx, len(pattern_index_map)) if pattern_index_map else base

            color_box = tk.Label(row, width=2, background=shade, relief="groove")
            color_box.pack(side=tk.LEFT, padx=(0, 5))

            var = tk.BooleanVar(value=pat.get("enabled", True))
            chk = ttk.Checkbutton(
                row,
                text=pat["name"],
                variable=var,
                command=lambda p=pat, v=var: self._on_toggle(p, v)
            )
            chk.pack(side=tk.LEFT, fill="x", expand=True)

            self.check_vars[pat["name"]] = var
            self.checkboxes[pat["name"]] = chk

    def _on_toggle(self, pattern, var):
        pattern["enabled"] = var.get()
        if self.on_toggle_callback:
            self.on_toggle_callback()
