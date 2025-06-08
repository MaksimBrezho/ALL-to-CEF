import os
import tkinter as tk
from tkinter import ttk, messagebox
from utils.i18n import translate as _

from utils.transform_logic import apply_transform

from gui.transform_editor import TransformEditorDialog
from utils import json_utils, code_generator
from utils.window_utils import set_window_icon


class CodeGeneratorDialog(tk.Toplevel):
    """Dialog for configuring and generating CEF converter code."""

    MANDATORY_FIELDS = [
        "deviceVendor",
        "deviceProduct",
        "deviceVersion",
        "signatureID",
        "name",
        "severity",
    ]

    CONSTANT_FIELDS = {"deviceVendor", "deviceProduct", "deviceVersion"}

    def __init__(self, parent, per_log_patterns=None, logs=None, log_key=None):
        super().__init__(parent)
        set_window_icon(self)
        self.title(_("CEF Code Generator Dialog"))
        self.minsize(700, 500)
        self.per_log_patterns = per_log_patterns or []
        self.logs = logs or []
        self.log_key = log_key

        config = json_utils.load_conversion_config(log_key)
        loaded = config.get("mappings") or []
        initial = self._build_initial_mappings()
        self.mappings = self._merge_mappings(loaded, initial)
        self._build_ui()
        self.bind_all("<Control-s>", lambda e: self._save_config())
        self.bind_all("<Control-p>", lambda e: self._on_preview())
        self.bind_all("<Control-g>", lambda e: self._on_generate())
        header_data = config.get("header", {})
        for key, var in self.header_vars.items():
            var.set(header_data.get(key, var.get()))

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label=_("Save Config"), command=self._save_config, accelerator="Ctrl+S")
        file_menu.add_command(label=_("Preview Code ▸"), command=self._on_preview, accelerator="Ctrl+P")
        file_menu.add_command(label=_("Generate Python"), command=self._on_generate, accelerator="Ctrl+G")
        menu_bar.add_cascade(label=_("Actions"), menu=file_menu)
        self.config(menu=menu_bar)

        header = ttk.LabelFrame(self, text=_("CEF Header"))
        header.pack(fill="x", padx=10, pady=5)

        self.header_vars = {}
        fields = [
            ("CEF Version", "0"),
            ("Device Vendor", "ACME"),
            ("Device Product", "LogParserPro"),
            ("Device Version", "1.0.0"),
            ("Event Class ID", "42"),
            ("Event Name", "LoginAttempt"),
            ("Severity (int)", "5"),
        ]
        for label, default in fields:
            var = tk.StringVar(value=default)
            self.header_vars[label] = var

        ttk.Label(header, text="CEF Version:").grid(row=0, column=0, sticky="w", pady=2, padx=2)
        entry = ttk.Entry(header, textvariable=self.header_vars["CEF Version"], state="disabled")
        entry.grid(row=0, column=1, sticky="ew", pady=2, padx=2)
        header.grid_columnconfigure(1, weight=1)

        self.mapping_frame = ttk.LabelFrame(self, text=_("Fields Auto-Mapped from Regex Patterns"))
        self.mapping_frame.pack(fill="both", expand=True, padx=10, pady=5)
        canvas = tk.Canvas(self.mapping_frame)
        scroll = ttk.Scrollbar(self.mapping_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.mapping_list = ttk.Frame(canvas)
        self.mapping_list.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.mapping_list, anchor="nw")

        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=5)
        ttk.Button(btns, text=_("+ Add Field"), command=self._on_add_field).pack(side="left", padx=5)

        self._refresh_mapping_list()

    def _build_initial_mappings(self):
        # Only consider patterns that are present for this log file
        patterns = list(self.per_log_patterns)
        cef_fields = json_utils.load_cef_fields()
        cef_keys = {f.get("key") for f in cef_fields}
        time_fields = {f.get("key") for f in cef_fields if f.get("category") == "Time"}

        by_field = {}
        for p in patterns:
            name = p.get("name")
            fields = p.get("fields", [])

            for fld in fields:
                if fld in cef_keys:
                    by_field.setdefault(fld, []).append(name)

            if name in cef_keys:
                by_field.setdefault(name, []).append(name)

        mappings: list[dict] = []
        for field in self.MANDATORY_FIELDS:
            names = by_field.get(field, [])
            if field in self.CONSTANT_FIELDS and not names:
                mappings.append({"cef": field, "pattern": "", "value": "", "transform": "none"})
                continue
            if not names:
                if field == "signatureID":
                    mappings.append({"cef": field, "rule": "incremental", "transform": "none"})
                else:
                    mappings.append({"cef": field, "pattern": "", "value": "", "transform": "none"})
            else:
                for n in names:
                    transform = "time" if field in time_fields else "none"
                    mappings.append({"cef": field, "pattern": n, "value": "", "transform": transform})

        for field, names in by_field.items():
            if field in self.MANDATORY_FIELDS or field in self.CONSTANT_FIELDS:
                continue
            for n in names:
                transform = "time" if field in time_fields else "none"
                mappings.append({"cef": field, "pattern": n, "value": "", "transform": transform})

        return mappings

    def _merge_mappings(self, existing: list[dict], initial: list[dict]) -> list[dict]:
        """Merge mappings loaded from config with defaults based on current patterns."""
        def _is_placeholder(mapping: dict) -> bool:
            """Return True if the mapping represents an empty default entry."""
            return (
                not mapping.get("pattern")
                and not mapping.get("value")
                and mapping.get("rule") is None
            ) or (
                mapping.get("rule") == "incremental"
                and not mapping.get("pattern")
                and not mapping.get("value")
            )

        merged = list(existing)
        seen = {
            (m.get("cef"), m.get("pattern"), m.get("value"), m.get("rule"))
            for m in merged
        }
        for m in initial:
            key = (m.get("cef"), m.get("pattern"), m.get("value"), m.get("rule"))
            if key in seen:
                continue

            if _is_placeholder(m):
                if any(e.get("cef") == m.get("cef") for e in existing):
                    # Skip placeholder if a mapping for this field already exists
                    continue
            else:
                # Remove placeholder mapping for the same field
                for idx in range(len(merged) - 1, -1, -1):
                    current = merged[idx]
                    if current.get("cef") == m.get("cef") and _is_placeholder(current):
                        del merged[idx]
                        seen.discard(
                            (
                                current.get("cef"),
                                current.get("pattern"),
                                current.get("value"),
                                current.get("rule"),
                            )
                        )

            merged.append(m)
            seen.add(key)
        return merged

    # ------------------------------------------------------------------
    # helpers
    def _collect_patterns(self) -> list:
        patterns = {p["name"]: p for p in json_utils.load_all_patterns()}
        for p in self.per_log_patterns:
            patterns[p.get("name")] = p

        result = []
        for name, pat in patterns.items():
            entry = {
                "name": name,
                "regex": pat.get("regex", pat.get("pattern", "")),
            }
            if "fields" in pat:
                entry["fields"] = pat["fields"]
            result.append(entry)
        return result

    def _find_example(self, regex: str) -> str:
        import re

        try:
            pat = re.compile(regex)
        except re.error:
            return ""
        for line in self.logs:
            m = pat.search(line)
            if m:
                return m.group(0)
        return ""

    def _find_examples(self, regex: str, max_lines: int = 5) -> list[str]:
        """Return unique matched segments for the regex."""
        import re

        try:
            pat = re.compile(regex)
        except re.error:
            return []

        result = []
        seen = set()
        for line in self.logs:
            m = pat.search(line)
            if not m:
                continue

            value = m.group(0)

            if value not in seen:
                seen.add(value)
                result.append(value)
                if len(result) >= max_lines:
                    break
        return result

    def _get_transformed_example(self, regex: str, transform: object, value: str = "") -> str:
        """Return an example value after applying the transform."""
        raw = self._find_example(regex) if regex else value
        if not raw:
            return ""
        return apply_transform(raw, transform)

    def _choose_cef_field(self):
        keys = json_utils.load_cef_field_keys()
        if not keys:
            messagebox.showerror(_("Error"), _("No CEF fields available"))
            return None
        dlg = tk.Toplevel(self)
        set_window_icon(dlg)
        dlg.title(_("Choose CEF Field"))
        var = tk.StringVar(value=keys[0])
        combo = ttk.Combobox(dlg, values=keys, textvariable=var, state="readonly")
        combo.pack(padx=10, pady=10)
        result = {"val": None}

        def ok():
            result["val"] = var.get()
            dlg.destroy()

        ttk.Button(dlg, text=_("OK"), command=ok).pack(pady=5)
        dlg.grab_set()
        self.wait_window(dlg)
        return result["val"]

    def _on_add_field(self):
        field = self._choose_cef_field()
        if not field:
            return
        self.mappings.append({"cef": field, "pattern": "", "value": "", "transform": "none"})
        self._refresh_mapping_list()
        self._save_config()

    def _on_pattern_changed(self, idx, var):
        self.mappings[idx]["pattern"] = var.get()
        if var.get():
            self.mappings[idx]["value"] = ""
        self._refresh_mapping_list()
        self._save_config()

    def _on_value_changed(self, idx, var):
        self.mappings[idx]["value"] = var.get()
        self._save_config()

    def _on_edit_transform(self, idx):
        m = self.mappings[idx]
        cef_info = {f.get("key"): f for f in json_utils.load_cef_fields()}
        if cef_info.get(m.get("cef"), {}).get("category") == "Time":
            messagebox.showwarning(
                "Time Field",
                "Time values will be automatically converted to ISO-8601"
            )
        pattern_map = {p["name"]: p for p in self._collect_patterns()}
        regex = pattern_map.get(m.get("pattern"), {}).get("regex", "")
        examples = self._find_examples(regex) if regex else []
        if regex and not examples:
            ex = self._find_example(regex)
            if ex:
                examples = [ex]
        dlg = TransformEditorDialog(
            self,
            m["cef"],
            current=m["transform"],
            regex=regex,
            examples=examples,
            logs=self.logs,
        )
        dlg.grab_set()
        self.wait_window(dlg)
        if dlg.result is not None:
            m["transform"] = dlg.result
            self._refresh_mapping_list()
            self._save_config()

    def _on_remove_field(self, idx):
        del self.mappings[idx]
        self._refresh_mapping_list()
        self._save_config()

    def _gather_mappings(self):
        result = []
        for m in self.mappings:
            if m["cef"] in self.CONSTANT_FIELDS and not m.get("pattern"):
                result.append({"cef": m["cef"], "value": m.get("value", ""), "transform": m.get("transform", "none")})
            elif m.get("pattern"):
                result.append({"cef": m["cef"], "pattern": m["pattern"], "group": 0, "transform": m["transform"]})
            elif m.get("value"):
                result.append({"cef": m["cef"], "value": m["value"], "transform": m["transform"]})
            elif m.get("rule"):
                result.append({"cef": m["cef"], "rule": m["rule"], "transform": m["transform"]})
        return result


    # ------------------------------------------------------------------
    def _on_preview(self):
        import tempfile, pathlib

        # Use only the CEF version for code generation. Remaining header values
        # are provided via constant mappings.
        header = {"CEF Version": self.header_vars["CEF Version"].get()}
        mappings = self._gather_mappings()
        patterns = self._collect_patterns()

        tmp_dir = tempfile.mkdtemp()
        paths = code_generator.generate_files(header, mappings, patterns, tmp_dir)
        converter_path = pathlib.Path(paths[0])
        try:
            with open(converter_path, "r", encoding="utf-8") as f:
                data = f.read()
        except OSError as e:
            messagebox.showerror(_("Error"), str(e))
            return

        preview = tk.Toplevel(self)
        set_window_icon(preview)
        preview.title(_("Generated cef_converter.py"))
        text = tk.Text(preview, wrap="none")
        text.insert("1.0", data)
        text.pack(fill="both", expand=True)

    def _on_generate(self):
        # When generating files, only pass the CEF version. Other header values
        # should be supplied via constant mappings.
        header = {"CEF Version": self.header_vars["CEF Version"].get()}
        mappings = self._gather_mappings()
        patterns = self._collect_patterns()
        out_dir = os.path.join(os.getcwd(), "generated_cef")
        try:
            code_generator.generate_files(header, mappings, patterns, out_dir)
            messagebox.showinfo(_("Success"), _(f"Files written to {out_dir}"))
        except Exception as e:
            messagebox.showerror(_("Error"), str(e))

    # ------------------------------------------------------------------
    def _add_scrolled_label(self, parent, text: str, row: int, column: int):
        widget = tk.Text(parent, height=2, width=40, wrap="word")
        widget.insert("1.0", text)
        widget.configure(state="disabled")
        widget.grid(row=row, column=column, sticky="ew", padx=2)

    # ------------------------------------------------------------------
    def _refresh_mapping_list(self):
        for child in self.mapping_list.winfo_children():
            child.destroy()

        headers = [
            _("CEF Field"),
            _("Pattern"),
            _("Regex"),
            _("Transform"),
            _("Example"),
            _("Result"),
            "",
        ]
        for col, text in enumerate(headers):
            ttk.Label(
                self.mapping_list, text=text, font=("Segoe UI", 9, "bold")
            ).grid(row=0, column=col, sticky="w", padx=2)

        transform_labels = {
            "none": _("as is"),
            "lower": _("lower case"),
            "upper": _("UPPER CASE"),
            "capitalize": _("Capitalized"),
            "sentence": _("Sentence case"),
            "custom": _("Custom"),
        }

        pattern_map = {p["name"]: p for p in self._collect_patterns()}
        all_names = list(pattern_map.keys())

        counts = {}
        for m in self.mappings:
            counts[m["cef"]] = counts.get(m["cef"], 0) + 1
        used = {}

        for idx, m in enumerate(self.mappings, start=1):
            if m.get("rule") == "incremental":
                regex = ""
                example = "automatic"
                transformed = "automatic"
            else:
                pat_name = "" if m["cef"] in self.CONSTANT_FIELDS and not m.get("pattern") else m.get("pattern")
                regex = pattern_map.get(pat_name, {}).get("regex", "")
                example = self._find_example(regex) if regex else m.get("value", "")
                transformed = self._get_transformed_example(
                    regex, m.get("transform", "none"), m.get("value", "")
                )

            label = m["cef"]
            if counts.get(label, 0) > 1:
                used[label] = used.get(label, 0) + 1
                label = f"{label} {used[label]}"
            ttk.Label(self.mapping_list, text=label).grid(row=idx, column=0, sticky="w", padx=2)
            if m["cef"] in self.CONSTANT_FIELDS and not m.get("pattern"):
                var = tk.StringVar(value=m.get("value", ""))
                entry = ttk.Entry(self.mapping_list, textvariable=var)
                entry.grid(row=idx, column=1, sticky="ew", padx=2)
                entry.bind("<KeyRelease>", lambda e, i=idx-1, v=var: self._on_value_changed(i, v))
            elif m.get("pattern"):
                var = tk.StringVar(value=m["pattern"])
                combo = ttk.Combobox(self.mapping_list, values=all_names, textvariable=var, state="readonly")
                combo.grid(row=idx, column=1, sticky="ew", padx=2)
                combo.bind("<<ComboboxSelected>>", lambda e, i=idx-1, v=var: self._on_pattern_changed(i, v))
            else:
                var = tk.StringVar(value=m.get("value", ""))
                if m.get("rule") == "incremental":
                    ttk.Label(self.mapping_list, text="automatic").grid(row=idx, column=1, sticky="w", padx=2)
                else:
                    entry = ttk.Entry(self.mapping_list, textvariable=var)
                    entry.grid(row=idx, column=1, sticky="ew", padx=2)
                    entry.bind("<KeyRelease>", lambda e, i=idx-1, v=var: self._on_value_changed(i, v))
            self._add_scrolled_label(self.mapping_list, regex, idx, 2)
            btn_key = m["transform"] if isinstance(m.get("transform"), str) else "custom"
            btn_text = transform_labels.get(btn_key, btn_key)
            state = "normal"
            if (
                m["cef"] in self.CONSTANT_FIELDS or m["cef"] == "signatureID"
            ) and not m.get("pattern") and m.get("rule") != "incremental":
                state = "disabled"
            ttk.Button(self.mapping_list, text=btn_text, state=state, command=lambda i=idx-1: self._on_edit_transform(i)).grid(row=idx, column=3, sticky="w", padx=2)
            self._add_scrolled_label(self.mapping_list, example, idx, 4)
            self._add_scrolled_label(self.mapping_list, transformed, idx, 5)
            if m["cef"] not in self.MANDATORY_FIELDS:
                ttk.Button(self.mapping_list, text="✖", width=2, command=lambda i=idx-1: self._on_remove_field(i)).grid(row=idx, column=6, sticky="e", padx=2)

        self.mapping_list.grid_columnconfigure(1, weight=1)

    # ------------------------------------------------------------------
    def _save_config(self):
        # Only persist the CEF version in the header. Other values are derived
        # from mappings and should not be saved.
        header = {"CEF Version": self.header_vars["CEF Version"].get()}
        data = {"header": header, "mappings": self.mappings}
        json_utils.save_conversion_config(data, self.log_key)

    def _on_close(self):
        self._save_config()
        self.destroy()


