import tkinter as tk
from tkinter import ttk


from gui.transform_editor import TransformEditorDialog


def test_parse_mapping():
    text = "info=1\nerror=8\n"
    result = TransformEditorDialog._parse_mapping(text)
    assert result == {"info": "1", "error": "8"}


class DummyVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, v):
        self.value = v


class DummyText:
    def __init__(self, text):
        self.text = text

    def get(self, start, end):
        return self.text


def test_get_spec():
    dlg = TransformEditorDialog.__new__(TransformEditorDialog)
    dlg.var = DummyVar("upper")
    dlg.map_text = DummyText("info=1\nerror=8\n")
    dlg.replace_pattern_var = DummyVar("foo")
    dlg.replace_with_var = DummyVar("BAR")
    dlg.token_order = []
    dlg.tokens = []
    dlg.regex = ""

    spec = TransformEditorDialog._get_spec(dlg)
    assert spec == {
        "format": "upper",
        "value_map": {"info": "1", "error": "8"},
        "replace_pattern": "foo",
        "replace_with": "BAR",
    }


def test_get_spec_token_order():
    dlg = TransformEditorDialog.__new__(TransformEditorDialog)
    dlg.var = DummyVar("lower")
    dlg.map_text = DummyText("")
    dlg.replace_pattern_var = DummyVar("")
    dlg.replace_with_var = DummyVar("")
    dlg.token_order = [1, 0]
    dlg.tokens = ["a", "b"]
    dlg.regex = r"(\w+) (\w+)"

    spec = TransformEditorDialog._get_spec(dlg)
    assert spec == {"format": "lower", "token_order": [1, 0], "regex": r"(\w+) (\w+)"}


def test_init_token_editor_sets_tokens(monkeypatch):
    dlg = TransformEditorDialog.__new__(TransformEditorDialog)
    dlg.regex = r"user=(\w+)"
    dlg.examples = ["user=jane"]

    # Avoid actual tkinter widgets
    class DummyWidget:
        def __init__(self, *a, **k):
            pass

        def pack(self, *a, **k):
            pass

        def bind(self, *a, **k):
            pass

        def config(self, *a, **k):
            pass

        def yview(self, *a, **k):
            pass

        def set(self, *a, **k):
            pass

    monkeypatch.setattr(ttk, "Label", DummyWidget)
    monkeypatch.setattr(ttk, "Frame", DummyWidget)
    monkeypatch.setattr(ttk, "LabelFrame", DummyWidget)
    monkeypatch.setattr(ttk, "Button", DummyWidget)
    dlg.token_adv_frame = DummyWidget()
    monkeypatch.setattr(TransformEditorDialog, "_refresh_token_list", lambda self: None)

    TransformEditorDialog._init_token_editor(dlg)

    assert dlg.tokens == ["user=", "jane"]
    assert dlg.token_order == [0, 1]


def test_init_token_editor_split_on_no_groups(monkeypatch):
    dlg = TransformEditorDialog.__new__(TransformEditorDialog)
    dlg.regex = r"\d{2}/\d{2}/\d{4}"
    dlg.examples = ["01/02/2024"]

    class DummyWidget:
        def __init__(self, *a, **k):
            pass

        def pack(self, *a, **k):
            pass

        def bind(self, *a, **k):
            pass

    monkeypatch.setattr(ttk, "Label", DummyWidget)
    monkeypatch.setattr(ttk, "Frame", DummyWidget)
    monkeypatch.setattr(ttk, "LabelFrame", DummyWidget)
    monkeypatch.setattr(ttk, "Button", DummyWidget)
    dlg.token_adv_frame = DummyWidget()
    monkeypatch.setattr(TransformEditorDialog, "_refresh_token_list", lambda self: None)

    TransformEditorDialog._init_token_editor(dlg)

    assert dlg.tokens == ["01", "/", "02", "/", "2024"]
    assert dlg.token_order == [0, 1, 2, 3, 4]


def test_reset_tokens(monkeypatch):
    dlg = TransformEditorDialog.__new__(TransformEditorDialog)
    dlg.tokens = ["a", "b", "c"]
    dlg.token_order = [2, 1]
    dlg.token_adv_frame = None
    monkeypatch.setattr(TransformEditorDialog, "_refresh_token_list", lambda s: setattr(s, "called", True))
    dlg._update_example_box = lambda: None
    TransformEditorDialog._reset_tokens(dlg)
    assert dlg.token_order == [0, 1, 2]
    assert dlg.called


def test_toggle_token_editor(monkeypatch):
    dlg = TransformEditorDialog.__new__(TransformEditorDialog)

    class DummyFrame:
        def __init__(self):
            self.visible = False
        def pack(self, *a, **k):
            self.visible = True
        def forget(self):
            self.visible = False

    dlg.token_adv_frame = DummyFrame()
    dlg.show_token_editor = DummyVar(True)
    TransformEditorDialog._toggle_token_editor(dlg)
    assert dlg.token_adv_frame.visible
    dlg.show_token_editor.set(False)
    TransformEditorDialog._toggle_token_editor(dlg)
    assert not dlg.token_adv_frame.visible

def test_drag_updates_token_order(monkeypatch):
    dlg = TransformEditorDialog.__new__(TransformEditorDialog)

    class DummyFrame:
        def winfo_rootx(self):
            return 0

    class DummyLabel:
        def __init__(self, idx):
            self.token_idx = idx
            self._x = idx * 10
        def winfo_x(self):
            return self._x
        def winfo_width(self):
            return 8
        def pack_forget(self, *a, **k):
            pass
        def pack(self, *a, **k):
            pass

    dlg.token_frame = DummyFrame()
    dlg.token_widgets = [DummyLabel(0), DummyLabel(1), DummyLabel(2)]
    dlg.token_order = [0, 1, 2]

    class DummyEvent:
        def __init__(self, widget=None, x_root=0):
            self.widget = widget
            self.x_root = x_root

    dlg._on_drag_start(DummyEvent(widget=dlg.token_widgets[0]))
    # simulate dragging far to the right so the item moves to the end
    dlg._on_drag_motion(DummyEvent(widget=dlg.token_widgets[0], x_root=50))
    dlg._on_drag_stop(DummyEvent(widget=dlg.token_widgets[0]))

    assert dlg.token_order == [1, 2, 0]


def test_drag_updates_example(monkeypatch):
    dlg = TransformEditorDialog.__new__(TransformEditorDialog)

    class DummyFrame:
        def winfo_rootx(self):
            return 0

    class DummyLabel:
        def __init__(self, idx):
            self.token_idx = idx
            self._x = idx * 10
        def winfo_x(self):
            return self._x
        def winfo_width(self):
            return 8
        def pack_forget(self, *a, **k):
            pass
        def pack(self, *a, **k):
            pass

    dlg.token_frame = DummyFrame()
    dlg.token_widgets = [DummyLabel(0), DummyLabel(1), DummyLabel(2)]
    dlg.token_order = [0, 1, 2]

    called = {}
    def fake_update():
        called['hit'] = True
    dlg._update_example_box = fake_update

    class DummyEvent:
        def __init__(self, widget=None, x_root=0):
            self.widget = widget
            self.x_root = x_root

    dlg._on_drag_start(DummyEvent(widget=dlg.token_widgets[0]))
    dlg._on_drag_motion(DummyEvent(widget=dlg.token_widgets[0], x_root=50))

    assert called.get('hit')


def test_update_example_box_shows_context(monkeypatch):
    dlg = TransformEditorDialog.__new__(TransformEditorDialog)

    dlg.regex = r"[a-zA-Z]+ {1,2}\d{1,2}\ \d{2}:\d{2}:\d{2}(?= combo)"
    dlg.examples = ["Jun 14 15:16:01"]
    dlg.logs = ["Jun 14 15:16:01 combo"]
    dlg.var = DummyVar("none")
    dlg.map_text = DummyText("")
    dlg.replace_pattern_var = DummyVar("")
    dlg.replace_with_var = DummyVar("")
    dlg.token_order = []
    dlg.tokens = []

    actions = []

    class DummyBox:
        def config(self, **k):
            actions.append(("config", k))

        def delete(self, *a):
            actions.append(("delete", a))

        def insert(self, index, text, tag=None):
            actions.append(("insert", text, tag))

        def tag_configure(self, tag, **opts):
            actions.append(("tag", tag, opts))

    dlg.example_box = DummyBox()

    TransformEditorDialog._update_example_box(dlg)

    # No context should be displayed in the example output
    assert ("insert", " combo", "context") not in actions


def test_update_example_box_reorders_with_lookahead(monkeypatch):
    dlg = TransformEditorDialog.__new__(TransformEditorDialog)

    dlg.regex = r"[a-zA-Z]+ {1,2}\d{1,2}\ \d{2}:\d{2}:\d{2}(?= combo)"
    dlg.examples = ["Jun 14 15:16:01"]
    dlg.logs = ["Jun 14 15:16:01 combo"]
    dlg.var = DummyVar("none")
    dlg.map_text = DummyText("")
    dlg.replace_pattern_var = DummyVar("")
    dlg.replace_with_var = DummyVar("")
    dlg.token_order = [2, 3, 4, 5, 6, 7, 8, 1, 0]
    dlg.tokens = list(range(9))

    actions = []

    class DummyBox:
        def config(self, **k):
            actions.append(("config", k))

        def delete(self, *a):
            actions.append(("delete", a))

        def insert(self, index, text, tag=None):
            actions.append(("insert", text, tag))

        def tag_configure(self, tag, **opts):
            actions.append(("tag", tag, opts))

    dlg.example_box = DummyBox()

    TransformEditorDialog._update_example_box(dlg)

    assert ("insert", "14 15:16:01 Jun", None) in actions

def test_update_example_box_formats_example_only(monkeypatch):
    dlg = TransformEditorDialog.__new__(TransformEditorDialog)

    dlg.regex = r"foo(?= bar)"
    dlg.examples = ["foo"]
    dlg.logs = ["foo bar"]
    dlg.var = DummyVar("upper")
    dlg.map_text = DummyText("")
    dlg.replace_pattern_var = DummyVar("")
    dlg.replace_with_var = DummyVar("")
    dlg.token_order = []
    dlg.tokens = []

    actions = []

    class DummyBox:
        def config(self, **k):
            actions.append(("config", k))

        def delete(self, *a):
            actions.append(("delete", a))

        def insert(self, index, text, tag=None):
            actions.append(("insert", text, tag))

        def tag_configure(self, tag, **opts):
            actions.append(("tag", tag, opts))

    dlg.example_box = DummyBox()

    TransformEditorDialog._update_example_box(dlg)

    # Context text should not be inserted in the new display
    assert ("insert", " bar", "context") not in actions
    # With a simple transform like 'upper', only the example text
    # should be transformed, not the surrounding log line
    assert ("insert", "FOO", None) in actions
