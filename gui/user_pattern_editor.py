import tkinter as tk
from tkinter import ttk, messagebox
from utils.i18n import translate as _

from utils import json_utils
from utils.window_utils import set_window_icon


class UserPatternEditorDialog(tk.Toplevel):
    """Dialog for viewing and editing user defined patterns."""

    def __init__(self, parent):
        super().__init__(parent)
        set_window_icon(self)
        self.title(_("User Patterns"))
        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label=_("Save"), command=self._save_all, accelerator="Ctrl+S")
        menu_bar.add_cascade(label=_("File"), menu=file_menu)
        self.config(menu=menu_bar)
        self.bind_all("<Control-s>", lambda e: self._save_all())
        self.patterns = [p for p in json_utils.load_all_patterns() if p.get("source") != "builtin"]
        self.selected_index = None
        self._build_ui()
        self.bind_all("<Control-u>", lambda e: self._update_current())
        self.bind_all("<Delete>", lambda e: self._delete_current())
        self.bind_all("<Control-n>", lambda e: self._add_new())

    # ------------------------------------------------------------------
    def _build_ui(self):
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        left = ttk.Frame(main)
        left.pack(side="left", fill="y")

        self.listbox = tk.Listbox(left, height=15)
        self.listbox.pack(side="left", fill="y")
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.listbox.yview)
        scroll.pack(side="left", fill="y")
        self.listbox.configure(yscrollcommand=scroll.set)

        for pat in self.patterns:
            self.listbox.insert(tk.END, pat.get("name", ""))
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))

        self.name_var = tk.StringVar()
        self.regex_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.fields_var = tk.StringVar()
        self.priority_var = tk.StringVar()
        self.keys_var = tk.StringVar()

        row = ttk.Frame(right)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=_("Name:")).pack(side="left")
        ttk.Entry(row, textvariable=self.name_var).pack(side="left", fill="x", expand=True)

        row = ttk.Frame(right)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=_("Regex:")).pack(side="left")
        ttk.Entry(row, textvariable=self.regex_var).pack(side="left", fill="x", expand=True)

        row = ttk.Frame(right)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=_("Category:")).pack(side="left")
        ttk.Entry(row, textvariable=self.category_var).pack(side="left", fill="x", expand=True)

        row = ttk.Frame(right)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=_("Fields (comma separated):")).pack(side="left")
        ttk.Entry(row, textvariable=self.fields_var).pack(side="left", fill="x", expand=True)

        row = ttk.Frame(right)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=_("Priority:")).pack(side="left")
        ttk.Entry(row, textvariable=self.priority_var).pack(side="left", fill="x", expand=True)

        row = ttk.Frame(right)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=_("Log Keys:")).pack(side="left")
        ttk.Entry(row, textvariable=self.keys_var).pack(side="left", fill="x", expand=True)

        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=5)
        ttk.Button(btns, text=_("Update"), command=self._update_current).pack(side="left", padx=5)
        ttk.Button(btns, text=_("Delete"), command=self._delete_current).pack(side="left", padx=5)
        ttk.Button(btns, text=_("Add"), command=self._add_new).pack(side="left", padx=5)

    # ------------------------------------------------------------------
    def _on_select(self, event=None):
        idxs = self.listbox.curselection()
        if not idxs:
            return
        self.selected_index = int(idxs[0])
        pat = self.patterns[self.selected_index]
        self.name_var.set(pat.get("name", ""))
        self.regex_var.set(pat.get("regex", ""))
        self.category_var.set(pat.get("category", ""))
        self.fields_var.set(",".join(pat.get("fields", [])))
        self.priority_var.set(str(pat.get("priority", "")))
        self.keys_var.set(",".join(pat.get("log_keys", [])))

    # ------------------------------------------------------------------
    def _update_current(self):
        if self.selected_index is None:
            return
        pat = self.patterns[self.selected_index]
        pat["name"] = self.name_var.get().strip()
        pat["regex"] = self.regex_var.get()
        cat = self.category_var.get().strip()
        if cat:
            pat["category"] = cat
        else:
            pat.pop("category", None)
        fields = [f.strip() for f in self.fields_var.get().split(";") if f.strip()]
        if not fields:
            fields = [f.strip() for f in self.fields_var.get().split(",") if f.strip()]
        if fields:
            pat["fields"] = fields
        else:
            pat.pop("fields", None)
        pr = self.priority_var.get().strip()
        if pr:
            try:
                pat["priority"] = int(pr)
            except ValueError:
                pat["priority"] = pr
        else:
            pat.pop("priority", None)
        keys = [k.strip() for k in self.keys_var.get().split(";") if k.strip()]
        if not keys:
            keys = [k.strip() for k in self.keys_var.get().split(",") if k.strip()]
        if keys:
            pat["log_keys"] = keys
        else:
            pat.pop("log_keys", None)

        self.listbox.delete(self.selected_index)
        self.listbox.insert(self.selected_index, pat.get("name", ""))
        self.listbox.selection_set(self.selected_index)

    # ------------------------------------------------------------------
    def _delete_current(self):
        if self.selected_index is None:
            return
        del self.patterns[self.selected_index]
        self.listbox.delete(self.selected_index)
        self.selected_index = None
        self.name_var.set("")
        self.regex_var.set("")
        self.category_var.set("")
        self.fields_var.set("")
        self.priority_var.set("")
        self.keys_var.set("")

    # ------------------------------------------------------------------
    def _add_new(self):
        pat = {"name": "NewPattern", "regex": ""}
        self.patterns.append(pat)
        self.listbox.insert(tk.END, pat.get("name"))
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(len(self.patterns) - 1)
        self._on_select()

    # ------------------------------------------------------------------
    def _save_all(self):
        json_utils.save_user_patterns(self.patterns)
        messagebox.showinfo(_("Saved"), _("User patterns saved."))
        self.destroy()
