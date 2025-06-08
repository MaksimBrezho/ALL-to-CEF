import tkinter as tk
from tkinter import ttk
from utils.window_utils import set_window_icon
from utils.i18n import translate as _


class AskStringDialog(tk.Toplevel):
    """Simple dialog for entering a string value."""

    def __init__(self, parent, title: str, prompt: str, initialvalue: str = ""):
        super().__init__(parent)
        set_window_icon(self)
        self.title(title)
        self.result = None

        ttk.Label(self, text=prompt).pack(padx=10, pady=(10, 5))

        self.var = tk.StringVar(value=initialvalue)
        entry = ttk.Entry(self, textvariable=self.var)
        entry.pack(fill="x", padx=10)
        entry.focus_set()

        btns = ttk.Frame(self)
        btns.pack(pady=10)
        ttk.Button(btns, text="OK", command=self._on_ok).pack(side="left", padx=5)
        ttk.Button(btns, text=_("Cancel"), command=self._on_cancel).pack(side="left", padx=5)

        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self._on_cancel())
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)

    def _on_ok(self):
        self.result = self.var.get()
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()
