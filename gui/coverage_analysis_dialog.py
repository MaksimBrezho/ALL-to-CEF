import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

from utils.i18n import translate as _
from utils.window_utils import set_window_icon
from utils.text_utils import line_number_ranges
import textwrap


class CoverageAnalysisDialog(tk.Toplevel):
    """Dialog showing log coverage statistics."""

    @staticmethod
    def _wrap_missing_lines(text: str, width: int = 70) -> str:
        """Wrap long missing line lists for display."""
        if not text:
            return ""
        return textwrap.fill(text, width=width)

    @classmethod
    def _calculate_row_height(
        cls, field_stats: dict, base_height: int, width: int = 70
    ) -> int:
        """Return row height based on wrapped missing line lengths."""
        max_lines = 1
        for _, (_, missing) in field_stats.items():
            missing_str = line_number_ranges(missing) if missing else ""
            wrapped = cls._wrap_missing_lines(missing_str, width=width)
            lines = len(wrapped.splitlines()) or 1
            if lines > max_lines:
                max_lines = lines
        return base_height * max_lines

    def __init__(self, parent, coverage: float, field_stats: dict):
        super().__init__(parent)
        set_window_icon(self)
        self.title(_("Coverage Analysis"))
        self.minsize(600, 300)
        self.geometry("700x400")
        self.resizable(True, True)

        self.coverage = coverage
        self.field_stats = field_stats

        ttk.Label(
            self,
            text=_("Coverage: {value}%").format(value=f"{coverage:.1f}"),
        ).pack(padx=10, pady=(10, 0))

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", pady=(0, 10), padx=10)
        ttk.Button(btn_frame, text=_("Copy"), command=self._copy).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(btn_frame, text=_("OK"), command=self.destroy).pack(side="left")

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        columns = ("field", "percent", "missing")
        style = ttk.Style()
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=10,
            style="Coverage.Treeview",
        )
        self.tree.heading("field", text=_("Field"))
        self.tree.heading("percent", text=_("Coverage (%)"))
        self.tree.heading("missing", text=_("Missing Lines"))
        self.tree.column("field", width=120, anchor="w", stretch=False)
        self.tree.column("percent", width=100, anchor="center", stretch=False)
        self.tree.column("missing", width=360, anchor="w", stretch=True)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        try:
            base_height = tkfont.nametofont("TkDefaultFont").metrics("linespace")
        except Exception:
            base_height = 20
        row_height = self._calculate_row_height(field_stats, base_height)
        style.configure("Coverage.Treeview", rowheight=row_height, borderwidth=1, relief="solid")

        for field, (percent, missing) in field_stats.items():
            missing_str = line_number_ranges(missing) if missing else ""
            missing_str = self._wrap_missing_lines(missing_str)
            self.tree.insert("", "end", values=(field, f"{percent:.1f}", missing_str))


        self.bind("<Escape>", lambda e: self.destroy())
        self.bind_all("<Control-c>", lambda e: self._copy())
        self.grab_set()

    def _copy(self):
        try:
            lines = [_("Coverage: {value}%").format(value=f"{self.coverage:.1f}")]
            for field, (percent, missing) in self.field_stats.items():
                line = f"{field}: {percent:.1f}%"
                if missing:
                    nums = line_number_ranges(missing)
                    line += _(" (missing: {lines})").format(lines=nums)
                lines.append(line)
            text = "\n".join(lines)
            self.clipboard_clear()
            self.clipboard_append(text)
        except Exception:
            pass