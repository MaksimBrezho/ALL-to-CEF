import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog
from gui.ask_string_dialog import AskStringDialog
from utils.i18n import translate as _, set_language, add_callback
from utils.json_utils import (
    load_all_patterns,
    load_cef_fields,
    get_log_name_for_file,
    get_log_keys_for_file,
    load_per_log_patterns_for_file,
    load_per_log_patterns_by_key,
    load_log_key_map,
    save_per_log_pattern,
)
from core.regex_highlighter import find_matches_in_line, apply_highlighting
from gui.pattern_panel import PatternPanel
from utils.color_utils import generate_distinct_colors
from gui.tooltip import ToolTip
from gui.pattern_wizard import PatternWizardDialog
from gui.code_generator_dialog import CodeGeneratorDialog
from gui.cef_field_dialog import CEFFieldDialog
from gui.user_pattern_editor import UserPatternEditorDialog
from utils.text_utils import compute_char_coverage, compute_field_line_stats
from gui.coverage_analysis_dialog import CoverageAnalysisDialog
import logging
import re
import os

logger = logging.getLogger(__name__)


class AppWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.logs = []
        self.page_size = 40
        self.current_page = 0
        self.patterns = []
        self.per_log_patterns = []
        self.tooltip = ToolTip(self)
        self.pattern_panel = None
        self.match_cache = {}  # lineno -> list of matches
        self.tag_map = {}
        self.cef_fields = load_cef_fields()
        self.language_var = tk.StringVar(value="English")

        self._setup_widgets()
        self._load_patterns()
        add_callback(self.refresh_translations)

    def _setup_widgets(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self.text_area = tk.Text(frame, wrap=tk.NONE)
        self.text_area.grid(row=0, column=0, sticky="nsew")

        y_scroll = tk.Scrollbar(frame, orient="vertical", command=self.text_area.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.text_area.config(yscrollcommand=y_scroll.set)

        x_scroll = tk.Scrollbar(frame, orient="horizontal", command=self.text_area.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.text_area.config(xscrollcommand=x_scroll.set)

        self.pattern_panel = PatternPanel(
            master=frame,
            patterns=[],
            on_toggle_callback=self.render_page,
            width=200
        )
        self.pattern_panel.grid(row=0, column=2, sticky="ns", padx=5)
        self.pattern_panel.grid_propagate(False)
        self.pattern_panel.cef_fields = self.cef_fields

        menubar = tk.Menu(self.master, tearoff=0)
        self.cmd_menu = tk.Menu(menubar, tearoff=0)
        self.cmd_menu.add_command(label=_("Load Log"), command=self.load_log_file, accelerator="Ctrl+O")
        self.cmd_menu.add_command(label=_("Save Patterns"), command=self.save_current_patterns, accelerator="Ctrl+S")
        self.cmd_menu.add_command(label=_("Code Generator"), command=self.open_code_generator, accelerator="Ctrl+G")
        self.cmd_menu.add_command(label=_("Coverage Analysis"), command=self.open_coverage_analysis, accelerator="Ctrl+L")
        self.cmd_menu.add_command(label=_("Edit User Patterns"), command=self.open_user_pattern_editor, accelerator="Ctrl+U")
        menubar.add_cascade(label=_("Commands"), menu=self.cmd_menu)
        self.lang_menu = tk.Menu(menubar, tearoff=0)
        self.lang_menu.add_radiobutton(
            label="English",
            variable=self.language_var,
            value="English",
            command=lambda: self._set_language('en')
        )
        self.lang_menu.add_radiobutton(
            label="Русский",
            variable=self.language_var,
            value="Русский",
            command=lambda: self._set_language('ru')
        )
        menubar.add_cascade(label=_("Language"), menu=self.lang_menu)
        self.master.config(menu=menubar)
        self.menubar = menubar
        self.master.bind_all("<Control-o>", lambda e: self.load_log_file())
        self.master.bind_all("<Control-s>", lambda e: self.save_current_patterns())
        self.master.bind_all("<Control-g>", lambda e: self.open_code_generator())
        self.master.bind_all("<Control-l>", lambda e: self.open_coverage_analysis())
        self.master.bind_all("<Control-u>", lambda e: self.open_user_pattern_editor())
        self.master.bind_all("<Alt-Left>", lambda e: self.prev_page())
        self.master.bind_all("<Alt-Right>", lambda e: self.next_page())
        self.master.bind_all("<Control-n>", lambda e: self.open_pattern_wizard())

        ctrl = tk.Frame(self)
        ctrl.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        self.prev_btn = tk.Button(ctrl, text=_("← Prev"), command=self.prev_page)
        self.prev_btn.pack(side="left", padx=5)
        self.next_btn = tk.Button(ctrl, text=_("Next →"), command=self.next_page)
        self.next_btn.pack(side="left", padx=5)

        self.lines_label = tk.Label(ctrl, text=_("Lines per page:"))
        self.lines_label.pack(side="left", padx=(20, 5))

        self.spinbox = tk.Spinbox(ctrl, from_=1, to=1000, width=5, command=self.update_page_size)
        self.spinbox.pack(side="left")
        self.spinbox.delete(0, tk.END)
        self.spinbox.insert(0, str(self.page_size))

        self.status_label = tk.Label(ctrl, text="")
        self.status_label.pack(side="left", padx=15)
        self.coverage_label = tk.Label(ctrl, text="")
        self.coverage_label.pack(side="left", padx=15)
        self.create_btn = tk.Button(ctrl, text=_("Create Pattern"), command=self.open_pattern_wizard)
        self.create_btn.pack(side="left", padx=5)
        self.text_area.bind("<Motion>", self.on_hover)
        self.text_area.bind("<Leave>", lambda e: self.tooltip.hidetip())

    def _load_patterns(self):
        self.patterns = load_all_patterns()

    def load_log_file(self):
        path = filedialog.askopenfilename(filetypes=[("Log files", "*.log *.txt"), ("All files", "*.*")])
        if not path:
            return
        self.source_path = path
        with open(path, "r", encoding="utf-8") as f:
            self.logs = [line.rstrip() for line in f.readlines()]
        self.current_page = 0
        self._cache_matches()
        self.render_page()

    def _cache_matches(self):
        self.match_cache = {}
        active_patterns = [p for p in self.patterns if p.get("enabled", True)]

        per_log_patterns = []
        log_keys = []
        if getattr(self, "source_path", None):
            per_log_patterns = load_per_log_patterns_for_file(self.source_path)
            log_keys = get_log_keys_for_file(self.source_path)
        self.per_log_patterns = per_log_patterns

        # merge per-log and global patterns by name, prefer per-log
        pattern_map = {}
        for p in per_log_patterns + active_patterns:
            name = p.get("name")
            if name not in pattern_map or p.get("source") == "per_log":
                pattern_map[name] = p

        self.per_log_patterns = per_log_patterns

        all_patterns = list(pattern_map.values())

        for i, line in enumerate(self.logs, start=1):
            self.match_cache[i] = find_matches_in_line(line, all_patterns, log_keys)

    def _compute_coverage(self, active_names) -> float:
        if not self.logs:
            return 0.0
        return compute_char_coverage(self.logs, self.match_cache, active_names)

    def render_page(self):
        self.text_area.delete(1.0, tk.END)

        start = self.current_page * self.page_size
        end = start + self.page_size
        visible_lines = self.logs[start:end]

        for line in visible_lines:
            self.text_area.insert(tk.END, line + "\n")

        # Собираем все паттерны, у которых были совпадения
        matched_names = set()
        for matches in self.match_cache.values():
            for m in matches:
                matched_names.add(m["name"])

        # visible_patterns = все найденные паттерны, включая лог-специфические
        all_known = self.patterns + getattr(self, "per_log_patterns", [])
        unique = {}
        for p in all_known:
            name = p.get("name")
            if name not in unique or p.get("source") == "per_log":
                unique[name] = p
        visible_patterns = [p for n, p in unique.items() if n in matched_names]


        # active_patterns = включённые пользователем
        active_patterns = [p for p in visible_patterns if p.get("enabled", True)]
        active_names = set(p["name"] for p in active_patterns)

        # Формируем color_map по всем категориям
        categories = sorted({
            cat
            for cat in (p.get("category") for p in visible_patterns)
            if cat is not None
        })
        color_map = {cat: color for cat, color in zip(categories, generate_distinct_colors(len(categories)))}

        # Собираем matches для текущей страницы, но с относительной нумерацией
        matches_to_show = {
            rel_lineno: self.match_cache.get(abs_lineno, [])
            for rel_lineno, abs_lineno in enumerate(range(start + 1, end + 1), start=1)
        }

        # Построим индекс оттенков: (category, regex) -> index
        pattern_keys = []
        seen = set()
        for matches in self.match_cache.values():
            for m in matches:
                key = (m["category"], m["regex"])
                if key not in seen:
                    pattern_keys.append(key)
                    seen.add(key)

        pattern_index_map = {key: i for i, key in enumerate(pattern_keys)}

        coverage = self._compute_coverage(active_names)
        self.coverage_label.config(text=_("Coverage: {value}%").format(value=f"{coverage:.1f}"))

        # Проверка на пересекающиеся паттерны
        def has_overlap(matches: list[dict]) -> bool:
            intervals = sorted((m["start"], m["end"]) for m in matches)
            for i in range(1, len(intervals)):
                if intervals[i][0] < intervals[i - 1][1]:
                    return True
            return False

        for line_num, matches in matches_to_show.items():
            if has_overlap(matches):
                logger.warning("Overlapping patterns on line %s:", line_num)
                for m in matches:
                    logger.warning(
                        "  - %s..%s → %s (%s)",
                        m['start'],
                        m['end'],
                        m['name'],
                        m['regex'],
                    )

        # Подсветка текста
        apply_highlighting(self.text_area, matches_to_show, active_names, color_map, tag_map=self.tag_map)

        # Обновление панели справа
        self.pattern_panel.patterns = visible_patterns
        self.pattern_panel.refresh(color_map=color_map, pattern_index_map=pattern_index_map)

        self._update_status()

    def update_page_size(self):
        try:
            self.page_size = max(1, int(self.spinbox.get()))
            self.current_page = 0
            self.render_page()
        except ValueError:
            pass

    def _update_status(self):
        total_pages = (len(self.logs) - 1) // self.page_size + 1 if self.logs else 0
        self.status_label.config(text=_("Page {current} of {total}").format(current=self.current_page + 1, total=total_pages))

    def next_page(self):
        if (self.current_page + 1) * self.page_size < len(self.logs):
            self.current_page += 1
            self.render_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def on_hover(self, event):
        try:
            index = self.text_area.index(f"@{event.x},{event.y}")
            tags = self.text_area.tag_names(index)
            names = [self.tag_map[t]["name"] for t in tags if t in self.tag_map]
            if len(names) > 1:
                self.tooltip.schedule(
                    "Patterns: " + ", ".join(names), event.x_root, event.y_root
                )
            else:
                self.tooltip.unschedule()
        except Exception:
            self.tooltip.unschedule()

    def open_pattern_wizard(self):
        selections = self.get_selected_lines()
        if not selections:
            messagebox.showwarning(_("No Selection"), _("Please select lines to generate a pattern."))
            return

        # Получаем CEF-поля и путь к лог-файлу
        cef_fields = getattr(self.pattern_panel, "cef_fields", [])
        source_file = getattr(self, "source_path", "example.log")

        # Default pattern set name
        default_name = get_log_name_for_file(source_file) or os.path.basename(source_file)
        log_name = simpledialog.askstring(
            _("Set Name"), _("Enter name for per-log patterns:"),
            initialvalue=default_name,
            parent=self
        )
        if log_name is None:
            return
        categories = sorted(set(p.get("category", "") for p in self.patterns))

        try:
            selected_lines = [s for s, _ in selections]
            fragment_context = [c for _, c in selections]
            wizard = PatternWizardDialog(
                parent=self,
                selected_lines=selected_lines,
                fragment_context=fragment_context,
                context_lines=self.logs,

                cef_fields=cef_fields,
                source_file=source_file,
                log_name=log_name,
                categories=categories
            )
            wizard.grab_set()
            self.wait_window(wizard)
            self._load_patterns()
            self._cache_matches()
            self.render_page()
        except Exception as e:
            logger.error("[PatternWizard] %s", e)
            messagebox.showerror(_("Error"), _(f"Failed to open wizard: {e}"))

    def open_code_generator(self):
        """Open the code generator dialog (stub)."""
        try:
            per_patterns = list(self.per_log_patterns)
            if not per_patterns:
                keys = list(load_log_key_map().keys())
                if keys:
                    prompt = _("Choose log file key:\n") + ", ".join(keys)
                    key = simpledialog.askstring(_("Log Key"), prompt, parent=self)
                    if key:
                        per_patterns = load_per_log_patterns_by_key(key)

            log_key = None
            if getattr(self, "source_path", None):
                log_key = get_log_name_for_file(self.source_path)
            dlg = CodeGeneratorDialog(self, per_log_patterns=per_patterns, logs=self.logs, log_key=log_key)
            dlg.grab_set()
        except Exception as e:
            logger.error("[CodeGenerator] %s", e)
            messagebox.showerror(_("Error"), _(f"Failed to open generator: {e}"))

    def open_user_pattern_editor(self):
        """Open dialog for editing user-defined patterns."""
        try:
            dlg = UserPatternEditorDialog(self)
            dlg.grab_set()
            self.wait_window(dlg)
            self._load_patterns()
            self._cache_matches()
            self.render_page()
        except Exception as e:
            logger.error("[UserPatternEditor] %s", e)
            messagebox.showerror(_("Error"), _(f"Failed to open editor: {e}"))

    def open_coverage_analysis(self):
        """Open coverage analysis dialog."""
        try:
            patterns = self.patterns + list(getattr(self, "per_log_patterns", []))
            pattern_fields = {p.get("name"): p.get("fields", []) for p in patterns}
            active_names = {p.get("name") for p in patterns if p.get("enabled", True)}
            coverage = self._compute_coverage(active_names)
            field_stats = compute_field_line_stats(
                self.logs, self.match_cache, active_names, pattern_fields
            )
            dlg = CoverageAnalysisDialog(self, coverage, field_stats)
            dlg.grab_set()
        except Exception as e:
            logger.error("[CoverageAnalysis] %s", e)
            messagebox.showerror(_("Error"), _(f"Failed to open analysis: {e}"))

    def get_selected_lines(self):
        """Return selected fragments along with their full line context."""
        try:
            start = self.text_area.index(tk.SEL_FIRST)
            end = self.text_area.index(tk.SEL_LAST)
        except tk.TclError:
            return []

        start_line = int(start.split('.')[0])
        end_line = int(end.split('.')[0])

        selections = []
        for line_no in range(start_line, end_line + 1):
            line_start = f"{line_no}.0"
            line_end = f"{line_no}.end"
            full_line = self.text_area.get(line_start, line_end)

            sel_start = start if line_no == start_line else line_start
            sel_end = end if line_no == end_line else line_end
            fragment = self.text_area.get(sel_start, sel_end)
            if fragment.strip():
                selections.append((fragment, full_line))

        return selections

    def save_current_patterns(self):
        if not getattr(self, "source_path", None):
            messagebox.showinfo(_("No File"), _("Load a log file first"))
            return

        default_name = get_log_name_for_file(self.source_path) or os.path.basename(self.source_path)
        dlg = AskStringDialog(
            self,
            _("Set Name"),
            _("Enter name for per-log patterns:"),
            initialvalue=default_name,
        )
        self.wait_window(dlg)
        log_name = dlg.result
        if log_name is None:
            return

        matched_names = set()
        for matches in self.match_cache.values():
            for m in matches:
                matched_names.add(m["name"])

        patterns_to_save = [
            p for p in self.patterns
            if p["name"] in matched_names and p.get("enabled", True)
        ]

        for pat in patterns_to_save:
            data = pat.copy()
            if data.get("source") == "builtin":
                dlg = CEFFieldDialog(
                    self,
                    self.cef_fields,
                    data.get("name", ""),
                    initial=data.get("fields", [])
                )
                dlg.grab_set()
                self.wait_window(dlg)
                if dlg.result is None:
                    continue
                data["fields"] = dlg.result

            save_per_log_pattern(self.source_path, data["name"], data, log_name=log_name)

        # Reload per-log patterns and matches so other dialogs see updates
        self._cache_matches()
        self.render_page()

        messagebox.showinfo(_("Done"), _("Patterns saved."))

    def _set_language(self, lang: str):
        self.language_var.set('Русский' if lang == 'ru' else 'English')
        set_language(lang)
        # refresh translations without recreating the window
        self.refresh_translations()


    def refresh_translations(self):
        self.cmd_menu.entryconfigure(0, label=_("Load Log"))
        self.cmd_menu.entryconfigure(1, label=_("Save Patterns"))
        self.cmd_menu.entryconfigure(2, label=_("Code Generator"))
        self.cmd_menu.entryconfigure(3, label=_("Coverage Analysis"))
        self.cmd_menu.entryconfigure(4, label=_("Edit User Patterns"))
        self.menubar.entryconfigure(0, label=_("Commands"))
        self.menubar.entryconfigure(1, label=_("Language"))
        self.prev_btn.config(text=_("← Prev"))
        self.next_btn.config(text=_("Next →"))
        self.lines_label.config(text=_("Lines per page:"))
        self.create_btn.config(text=_("Create Pattern"))
        self.master.title(_("LogParserHelper"))
        self.render_page()
