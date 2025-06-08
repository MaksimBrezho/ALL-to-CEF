import types
import tkinter as tk

from gui.app_window import AppWindow
from gui.pattern_panel import PatternPanel


class DummyVar:
    def __init__(self, value):
        self.value = value
    def get(self):
        return self.value
    def set(self, v):
        self.value = v


class DummyText:
    def __init__(self, lines):
        self.lines = lines
        self.selection = None
    def set_selection(self, start, end):
        self.selection = (start, end)
    def index(self, idx):
        if idx == tk.SEL_FIRST:
            if not self.selection:
                raise tk.TclError('no selection')
            return self.selection[0]
        if idx == tk.SEL_LAST:
            if not self.selection:
                raise tk.TclError('no selection')
            return self.selection[1]
        return idx
    def _parse(self, index):
        line_s, col_s = index.split('.')
        line = int(line_s)
        if col_s == 'end':
            col = len(self.lines[line-1])
        else:
            col = int(col_s)
        return line, col
    def get(self, start, end):
        sl, sc = self._parse(start)
        el, ec = self._parse(end)
        assert sl == el, 'multi-line get not supported in DummyText'
        line = self.lines[sl-1]
        return line[sc:ec]


def test_get_selected_lines_multi():
    app = AppWindow.__new__(AppWindow)
    app.text_area = DummyText(["foo bar", "baz qux"])
    app.text_area.set_selection("1.4", "2.3")
    result = AppWindow.get_selected_lines(app)
    assert result == [("bar", "foo bar"), ("baz", "baz qux")]


def test_get_selected_lines_none():
    app = AppWindow.__new__(AppWindow)
    app.text_area = DummyText(["line1"])
    result = AppWindow.get_selected_lines(app)
    assert result == []


def test_pattern_panel_on_toggle():
    panel = PatternPanel.__new__(PatternPanel)
    called = []
    panel.on_toggle_callback = lambda: called.append(True)
    pattern = {"enabled": True}
    PatternPanel._on_toggle(panel, pattern, DummyVar(False))
    assert pattern["enabled"] is False
    assert called == [True]


def test_appwindow_compute_coverage():
    app = AppWindow.__new__(AppWindow)
    app.logs = ["error 123", "abc 456", "def"]
    app.match_cache = {
        1: [{"name": "p1", "match": "error 123"}],
        2: [{"name": "p2", "match": "abc"}],
        3: []
    }
    coverage = AppWindow._compute_coverage(app, {"p1", "p2"})
    assert round(coverage, 1) == round(11 / 17 * 100, 1)


def test_cache_matches_respects_log_keys(monkeypatch):
    app = AppWindow.__new__(AppWindow)
    app.logs = ["Notification time out: 5"]
    app.patterns = [
        {
            "name": "A",
            "regex": "Notification time out",
            "source": "user",
            "log_keys": ["x"],
            "enabled": True,
            "priority": 1000,
        },
        {
            "name": "B",
            "regex": "Notification time out: \d+",
            "source": "builtin",
            "log_keys": ["x"],
            "enabled": True,
            "priority": 100,
        },
    ]
    app.source_path = "/fake/path"

    import gui.app_window as app_mod

    monkeypatch.setattr(app_mod, "get_log_keys_for_file", lambda path: ["x"])

    AppWindow._cache_matches(app)

    names = {m["name"] for m in app.match_cache[1]}
    assert names == {"A", "B"}
