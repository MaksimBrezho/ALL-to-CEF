import json
import types
import tkinter as tk

import gui.user_pattern_editor as upe
from utils import json_utils

class DummyVar:
    def __init__(self, value=""):
        self.value = value
    def get(self):
        return self.value
    def set(self, v):
        self.value = v

class DummyListbox:
    def __init__(self, items):
        self.items = list(items)
        self._sel = None
    def delete(self, idx):
        self.items.pop(idx)
    def insert(self, idx, val):
        self.items.insert(idx, val)
    def selection_clear(self, start, end):
        self._sel = None
    def selection_set(self, idx):
        self._sel = idx
    def curselection(self):
        return () if self._sel is None else (self._sel,)


def test_user_pattern_editor_delete_and_save(tmp_path, monkeypatch):
    user_file = tmp_path / "user.json"
    builtin_file = tmp_path / "builtin.json"
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump({"patterns": [{"name": "p1", "regex": "a"}, {"name": "p2", "regex": "b"}]}, f)
    with open(builtin_file, "w", encoding="utf-8") as f:
        json.dump({"patterns": []}, f)
    monkeypatch.setattr(json_utils, "USER_PATTERNS_PATH", str(user_file))
    monkeypatch.setattr(json_utils, "BUILTIN_PATTERNS_PATH", str(builtin_file))
    dlg = upe.UserPatternEditorDialog.__new__(upe.UserPatternEditorDialog)
    dlg.patterns = [p for p in json_utils.load_all_patterns() if p.get("source") != "builtin"]
    dlg.selected_index = 1
    dlg.listbox = DummyListbox([p.get("name", "") for p in dlg.patterns])
    dlg.name_var = DummyVar()
    dlg.regex_var = DummyVar()
    dlg.category_var = DummyVar()
    dlg.fields_var = DummyVar()
    dlg.priority_var = DummyVar()
    dlg.keys_var = DummyVar()
    dlg.destroy = lambda: None
    monkeypatch.setattr(upe.messagebox, "showinfo", lambda *a, **k: None)
    upe.UserPatternEditorDialog._on_select(dlg)
    upe.UserPatternEditorDialog._delete_current(dlg)
    with open(user_file, "r", encoding="utf-8") as f:
        saved = json.load(f)["patterns"]
    assert saved == [{"name": "p1", "regex": "a", "source": "user"}]