import tkinter as tk
from tkinter import ttk

from gui.pattern_wizard import PatternWizardDialog


class DummyVar:
    def __init__(self, value=None):
        self.value = value
    def get(self):
        return self.value
    def set(self, v):
        self.value = v
    def trace_add(self, mode, func):
        pass


class DummyFrame:
    def __init__(self):
        self.packed = False
        self.children = []
    def pack(self, *a, **k):
        self.packed = True
    def forget(self):
        self.packed = False
    def winfo_children(self):
        return list(self.children)
    def add_child(self, child):
        self.children.append(child)


class DummyEntry:
    def __init__(self):
        self.text = ""
    def delete(self, start, end):
        self.text = ""
    def insert(self, index, value):
        self.text += value
    def get(self, start="1.0", end="end"):
        return self.text


class DummyCheckbutton:
    def __init__(self, parent, text="", variable=None):
        self.parent = parent
        self.text = text
        self.variable = variable
        parent.add_child(self)
    def pack(self, *a, **k):
        pass
    def destroy(self):
        if self in self.parent.children:
            self.parent.children.remove(self)


def test_on_digit_mode_change():
    wiz = PatternWizardDialog.__new__(PatternWizardDialog)
    wiz.digit_mode_values = {"Fixed length": "always_fixed_length"}
    wiz.digit_mode_display_var = DummyVar("Fixed length")
    wiz.digit_mode_var = DummyVar()
    PatternWizardDialog._on_digit_mode_change(wiz)
    assert wiz.digit_mode_var.get() == "always_fixed_length"


def test_push_and_undo_history(monkeypatch):
    wiz = PatternWizardDialog.__new__(PatternWizardDialog)
    wiz.regex_history = ["a", "b"]
    wiz.regex_entry = DummyEntry()
    called = []
    monkeypatch.setattr(wiz, "_apply_regex", lambda: called.append(True))

    PatternWizardDialog._push_history(wiz, "b")
    PatternWizardDialog._push_history(wiz, "c")
    assert wiz.regex_history == ["a", "b", "c"]

    PatternWizardDialog._undo_regex(wiz)
    assert wiz.regex_history == ["a", "b"]
    assert wiz.regex_entry.get() == "b"
    assert called == [True]


def test_toggle_advanced():
    wiz = PatternWizardDialog.__new__(PatternWizardDialog)
    wiz.show_advanced = DummyVar(True)
    wiz.advanced_frame = DummyFrame()
    PatternWizardDialog._toggle_advanced(wiz)
    assert wiz.advanced_frame.packed is True
    wiz.show_advanced.set(False)
    PatternWizardDialog._toggle_advanced(wiz)
    assert wiz.advanced_frame.packed is False


def test_filter_cef_fields(monkeypatch):
    wiz = PatternWizardDialog.__new__(PatternWizardDialog)
    wiz.cef_search_var = DummyVar("")
    wiz.cef_field_inner = DummyFrame()
    wiz.cef_fields = [
        {"key": "src", "name": "Source", "example": "host"},
        {"key": "dst", "name": "Destination", "example": "server"},
    ]
    wiz.selected_field_vars = {}
    monkeypatch.setattr(tk, "BooleanVar", lambda: DummyVar(False))
    monkeypatch.setattr(ttk, "Checkbutton", DummyCheckbutton)
    monkeypatch.setattr(wiz, "_add_tip", lambda *a, **k: None)

    PatternWizardDialog._filter_cef_fields(wiz)
    assert [c.text for c in wiz.cef_field_inner.children] == ["src", "dst"]

    wiz.cef_search_var.set("dst")
    PatternWizardDialog._filter_cef_fields(wiz)
    assert [c.text for c in wiz.cef_field_inner.children] == ["dst"]


def test_auto_select_category_single():
    wiz = PatternWizardDialog.__new__(PatternWizardDialog)
    wiz.selected_field_vars = {"src": DummyVar(True)}
    wiz.cef_category_map = {"src": "Network"}
    wiz.categories = ["User", "Network"]
    wiz.category_var = DummyVar()

    wiz.MULTI_CATEGORY = "Multiple"

    PatternWizardDialog._auto_select_category(wiz)
    assert wiz.category_var.get() == "Network"


def test_auto_select_category_multi():
    wiz = PatternWizardDialog.__new__(PatternWizardDialog)
    wiz.selected_field_vars = {"src": DummyVar(True), "user": DummyVar(True)}
    wiz.cef_category_map = {"src": "Network", "user": "User"}
    wiz.categories = ["Network", "User", "Multiple"]
    wiz.category_var = DummyVar("Initial")
    wiz.MULTI_CATEGORY = "Multiple"
    PatternWizardDialog._auto_select_category(wiz)
    assert wiz.category_var.get() == "Multiple"


def test_on_snippet_selected():
    wiz = PatternWizardDialog.__new__(PatternWizardDialog)
    wiz.regex_entry = DummyEntry()
    wiz.snippet_var = DummyVar("Digits")
    wiz.snippet_map = {"Digits": "\\d+"}
    wiz.SNIPPET_DEFAULT = "Insert"

    PatternWizardDialog._on_snippet_selected(wiz)
    assert wiz.regex_entry.get() == "\\d+"
    assert wiz.snippet_var.get() == "Insert"

