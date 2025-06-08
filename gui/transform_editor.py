import tkinter as tk
from tkinter import ttk
from utils.i18n import translate as _

from utils.transform_logic import apply_transform
from utils.window_utils import set_window_icon


class TransformEditorDialog(tk.Toplevel):
    """Dialog for selecting a basic or advanced value transformation."""

    TRANSFORMS = [
        ("none", "as is"),
        ("lower", "lower case"),
        ("upper", "UPPER CASE"),
        ("capitalize", "Capitalized"),
        ("sentence", "Sentence case"),
    ]

    def __init__(
        self,
        parent,
        cef_field: str,
        current: object = "none",
        *,
        regex: str = "",
        examples: list[str] | None = None,
        logs: list[str] | None = None,
    ):
        super().__init__(parent)
        set_window_icon(self)
        self.result = None
        self.title(_(f"Transform Editor for CEF Field: {cef_field}"))
        self.minsize(300, 360)
        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label=_("Save"), command=self._on_save, accelerator="Ctrl+S")
        file_menu.add_command(label=_("Cancel"), command=self.destroy, accelerator="Esc")
        menu_bar.add_cascade(label=_("File"), menu=file_menu)
        self.config(menu=menu_bar)
        self.bind_all("<Control-s>", lambda e: self._on_save())
        self.bind_all("<Escape>", lambda e: self.destroy())
        self.examples = examples or []
        self.logs = logs or []
        self.regex = regex
        self.tokens = []
        self.token_order = []
        self.show_token_editor = tk.BooleanVar(value=False)
        if regex:
            ttk.Label(self, text=_("Regex:")).pack(anchor="w", padx=10, pady=(5, 0))
            regex_box = tk.Text(self, height=1, width=40)
            regex_box.insert("1.0", regex)
            regex_box.config(state="disabled")
            regex_box.pack(fill="x", padx=10)

        if self.examples:
            ttk.Label(self, text=_("Examples:")).pack(anchor="w", padx=10, pady=(5, 0))
            self.example_box = tk.Text(
                self, height=min(5, len(self.examples)), width=40
            )
            self.example_box.pack(fill="x", padx=10)
            self.example_box.config(state="disabled")

        token_order_current = None
        if isinstance(current, dict):
            fmt = current.get("format", "none")
            mapping_text = "\n".join(
                f"{k}={v}" for k, v in current.get("value_map", {}).items()
            )
            replace_pat = current.get("replace_pattern", "")
            replace_with = current.get("replace_with", "")
            if current.get("token_order"):
                try:
                    token_order_current = [int(i) for i in current["token_order"]]
                except Exception:
                    token_order_current = None
        else:
            fmt = str(current)
            mapping_text = ""
            replace_pat = ""
            replace_with = ""

        ttk.Label(self, text=_("Formatting:")).pack(anchor="w", padx=10, pady=(10, 5))
        self.var = tk.StringVar(value=fmt)
        for value, label in self.TRANSFORMS:
            ttk.Radiobutton(self, text=_(label), variable=self.var, value=value).pack(
                anchor="w", padx=20
            )
        self.var.trace_add("write", lambda *_: self._update_example_box())

        ttk.Label(self, text=_("Value map (key=value per line):")).pack(
            anchor="w", padx=10, pady=(10, 5)
        )
        self.map_text = tk.Text(self, height=4, width=40)
        self.map_text.pack(fill="x", padx=10)
        if mapping_text:
            self.map_text.insert("1.0", mapping_text)
        self.map_text.bind("<KeyRelease>", lambda e: self._update_example_box())
        apply_btn = ttk.Button(self, text=_("Apply"), command=self._update_example_box)
        apply_btn.pack(anchor="e", padx=10, pady=(0, 5))
        self.bind_all("<Control-Return>", lambda e: self._update_example_box())

        rep_frame = ttk.Frame(self)
        rep_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(rep_frame, text=_("Replace if pattern matches:")).grid(
            row=0, column=0, sticky="w"
        )
        self.replace_pattern_var = tk.StringVar(value=replace_pat)
        self.replace_with_var = tk.StringVar(value=replace_with)
        ttk.Entry(rep_frame, textvariable=self.replace_pattern_var).grid(
            row=1, column=0, sticky="ew"
        )
        ttk.Entry(rep_frame, textvariable=self.replace_with_var).grid(
            row=1, column=1, sticky="ew"
        )
        self.replace_pattern_var.trace_add(
            "write", lambda *_: self._update_example_box()
        )
        self.replace_with_var.trace_add("write", lambda *_: self._update_example_box())
        rep_frame.grid_columnconfigure(0, weight=1)
        rep_frame.grid_columnconfigure(1, weight=1)

        if self.regex:
            chk = ttk.Checkbutton(
                self,
                text=_("Show advanced token options"),
                variable=self.show_token_editor,
                command=self._toggle_token_editor,
            )
            chk.pack(anchor="w", padx=10, pady=(5, 0))
            self.token_adv_frame = ttk.Frame(self)
            self._init_token_editor()
            if token_order_current is not None and len(token_order_current) == len(self.tokens):
                self.token_order = token_order_current
                self._refresh_token_list()
            self._toggle_token_editor()

        # initial examples rendering
        self._update_example_box()

    # ------------------------------------------------------------------
    def _init_token_editor(self):
        import re

        pat = re.compile(self.regex)
        best = None
        search_space = getattr(self, "logs", []) or self.examples
        for line in search_space:
            m = pat.search(line)
            if not m:
                continue
            # choose the match with the most groups/longest span
            if (
                best is None
                or (m.lastindex or 0) > (best[0].lastindex or 0)
                or (
                    (m.lastindex or 0) == (best[0].lastindex or 0)
                    and m.end() - m.start() > best[0].end() - best[0].start()
                )
            ):
                best = (m, line)
        if best is None:
            return
        m, line = best
        value = line

        tokens = []
        if m.lastindex:
            pos = m.start()
            for i in range(1, (m.lastindex or 0) + 1):
                literal = value[pos : m.start(i)]
                if literal:
                    tokens.append(literal)
                tokens.append(m.group(i))
                pos = m.end(i)
            tail = value[pos : m.end()]
            if tail:
                tokens.append(tail)
        else:
            span = value[m.start() : m.end()]
            tokens = [t for t in re.split(r"([a-zA-Z]+|\d+|\W)", span) if t]

        self.tokens = tokens
        self.token_order = list(range(len(tokens)))

        frame = ttk.LabelFrame(
            self.token_adv_frame,
            text=_("Reorder tokens (drag to move, Del to remove)"),
        )
        frame.pack(fill="x")
        self.token_frame = ttk.Frame(frame)
        self.token_frame.pack(fill="x")
        self.token_widgets: list[ttk.Label] = []
        self._refresh_token_list()
        ttk.Button(frame, text=_("Reset"), command=self._reset_tokens).pack(anchor="e", padx=5, pady=(0, 5))

    def _refresh_token_list(self):
        if not hasattr(self, "token_frame"):
            return
        for w in getattr(self, "token_widgets", []):
            w.destroy()
        self.token_widgets = []
        for idx in self.token_order:
            lbl = ttk.Label(
                self.token_frame,
                text=self.tokens[idx],
                relief="raised",
                borderwidth=1,
                padding=(4, 2),
            )
            lbl.token_idx = idx
            lbl.pack(side="left", padx=2, pady=2)
            lbl.bind("<Button-1>", self._on_drag_start)
            lbl.bind("<B1-Motion>", self._on_drag_motion)
            lbl.bind("<ButtonRelease-1>", self._on_drag_stop)
            lbl.bind("<Delete>", self._delete_token)
            lbl.bind("<Double-Button-1>", self._delete_token)
            self.token_widgets.append(lbl)
        self.token_frame.update_idletasks()

    def _on_drag_start(self, event):
        widget = event.widget
        self._drag_widget = widget
        self._drag_index = self.token_widgets.index(widget)

    def _on_drag_motion(self, event):
        if not hasattr(self, "_drag_widget") or self._drag_widget is None:
            return
        x = event.x_root - self.token_frame.winfo_rootx()
        # allow inserting after the last element
        new_index = len(self.token_widgets)
        for i, w in enumerate(self.token_widgets):
            if w is self._drag_widget:
                continue
            mid = w.winfo_x() + w.winfo_width() / 2
            if x < mid:
                new_index = i
                break
        if new_index > self._drag_index:
            new_index -= 1
        if new_index != self._drag_index:
            w = self.token_widgets.pop(self._drag_index)
            self.token_widgets.insert(new_index, w)
            self.token_order = [wid.token_idx for wid in self.token_widgets]
            self._drag_index = new_index
            # Repack existing widgets instead of recreating them to
            # preserve the drag event bindings
            for widget in self.token_widgets:
                widget.pack_forget()
                widget.pack(side="left", padx=2, pady=2)
            self._update_example_box()

    def _on_drag_stop(self, event):
        self._drag_widget = None
        self._drag_index = None
        self._update_example_box()

    def _delete_token(self, event=None):
        if not hasattr(self, "token_widgets"):
            return
        if event is None:
            return
        widget = event.widget
        if widget not in self.token_widgets:
            return
        idx = self.token_widgets.index(widget)
        self.token_order.pop(idx)
        self.token_widgets.pop(idx)
        widget.destroy()
        self._refresh_token_list()
        self._update_example_box()

    def _reset_tokens(self):
        """Reset token order to the original state."""
        self.token_order = list(range(len(self.tokens)))
        self._refresh_token_list()
        self._update_example_box()

    def _toggle_token_editor(self):
        if not hasattr(self, "token_adv_frame"):
            return
        if self.show_token_editor.get():
            self.token_adv_frame.pack(fill="x", padx=10, pady=(0, 5))
        else:
            self.token_adv_frame.forget()

    @staticmethod
    def _parse_mapping(text: str) -> dict:
        mapping = {}
        for line in text.strip().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                mapping[k.strip()] = v.strip()
        return mapping

    def _get_spec(self) -> object:
        """Return the transformation spec from current UI values."""
        fmt = self.var.get()
        mapping = self._parse_mapping(self.map_text.get("1.0", "end"))
        replace_pat = self.replace_pattern_var.get().strip()
        replace_with = self.replace_with_var.get()

        result = {"format": fmt}
        if mapping:
            result["value_map"] = mapping
        if replace_pat:
            result["replace_pattern"] = replace_pat
            result["replace_with"] = replace_with
        if self.token_order:
            default = list(range(len(self.tokens)))
            if self.token_order != default:
                result["token_order"] = self.token_order
                result["regex"] = self.regex

        if list(result.keys()) == ["format"]:
            return result["format"]
        return result

    def _update_example_box(self):
        if not hasattr(self, "example_box"):
            return
        spec = self._get_spec()
        self.example_box.config(state="normal")
        self.example_box.delete("1.0", "end")
        if self.regex:
            import re

            try:
                pat = re.compile(self.regex)
            except re.error:
                pat = None
        else:
            pat = None

        self.example_box.tag_configure("context", foreground="gray")

        for ex in self.examples:
            prefix = ""
            suffix = ""
            line = ex
            if pat and self.logs:
                for line_text in self.logs:
                    m = pat.search(line_text)
                    if m and m.group(0) == ex:
                        prefix = line_text[: m.start()]
                        suffix = line_text[m.end() :]
                        line = line_text
                        break

            # Basic format-only transforms should operate on the raw
            # example text, while advanced token reordering may rely on
            # surrounding context from the full log line.  Use the full
            # line only when token_order is specified.
            target = line if isinstance(spec, dict) and "token_order" in spec else ex
            transformed_line = apply_transform(target, spec)

            # Only show the example before and after transformation.
            # Skip any surrounding log context for a cleaner display.
            self.example_box.insert("end", ex)
            self.example_box.insert("end", " -> ")
            self.example_box.insert("end", transformed_line)
            self.example_box.insert("end", "\n")

        self.example_box.config(state="disabled")

    def _on_save(self):
        result = self._get_spec()
        self.result = result
        self.destroy()
