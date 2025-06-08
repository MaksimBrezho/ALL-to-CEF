import tkinter as tk
from tkinter import ttk
from utils.i18n import translate as _
from utils.window_utils import set_window_icon


class CEFFieldDialog(tk.Toplevel):
    """Dialog for selecting CEF fields for a pattern."""

    def __init__(self, parent, cef_fields, pattern_name: str, initial=None):
        super().__init__(parent)
        set_window_icon(self)
        self.title(_(f"CEF Fields for {pattern_name}"))
        self.result = None
        self.var_map = {}
        self.cef_fields = cef_fields or []
        self.initial = set(initial or [])
        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(frame, height=200)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")

        for field in self.cef_fields:
            key = field.get("key", "")
            var = tk.BooleanVar(value=key in self.initial)
            chk = ttk.Checkbutton(inner, text=key, variable=var)
            chk.pack(anchor="w")
            self.var_map[key] = var

        btns = ttk.Frame(self)
        btns.pack(pady=5)
        ttk.Button(btns, text=_("OK"), command=self._on_ok).pack(side="left", padx=5)
        ttk.Button(btns, text=_("Cancel"), command=self._on_cancel).pack(side="left", padx=5)

    def _on_ok(self):
        self.result = [k for k, v in self.var_map.items() if v.get()]
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()
