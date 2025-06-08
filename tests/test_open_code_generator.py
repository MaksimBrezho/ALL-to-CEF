from gui.app_window import AppWindow
from utils import json_utils


def test_open_code_generator_selects_key(monkeypatch):
    app = AppWindow.__new__(AppWindow)
    app.per_log_patterns = []
    app.source_path = None
    app.logs = []

    monkeypatch.setattr(json_utils, "load_log_key_map", lambda: {"app": {"file": "log", "keys": []}})
    monkeypatch.setattr(json_utils, "load_per_log_patterns_by_key", lambda k: [{"name": "A", "regex": "foo", "source": "per_log"}])

    import gui.app_window as app_mod

    monkeypatch.setattr(app_mod, "load_log_key_map", lambda: {"app": {"file": "log", "keys": []}})
    monkeypatch.setattr(app_mod, "load_per_log_patterns_by_key", lambda k: [{"name": "A", "regex": "foo", "source": "per_log"}])
    monkeypatch.setattr(app_mod.simpledialog, "askstring", lambda *a, **k: "app")
    monkeypatch.setattr(app_mod.messagebox, "showerror", lambda *a, **k: None)

    captured = {}

    class DummyDialog:
        def __init__(self, parent, per_log_patterns=None, logs=None, log_key=None):
            captured["patterns"] = per_log_patterns
            captured["logs"] = logs
            captured["log_key"] = log_key
        def grab_set(self):
            pass

    monkeypatch.setattr(app_mod, "CodeGeneratorDialog", DummyDialog)

    AppWindow.open_code_generator(app)

    assert captured["patterns"][0]["name"] == "A"
    assert captured["logs"] == []
    assert captured["log_key"] is None
