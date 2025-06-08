import json


from utils import json_utils
from gui.app_window import AppWindow


def test_load_per_log_patterns_for_file(tmp_path, monkeypatch):
    file_path = tmp_path / "per.json"
    monkeypatch.setattr(json_utils, "PER_LOG_PATTERNS_PATH", str(file_path))
    data = {
        "log": {
            "file": "/var/log/app.log",
            "patterns": {
                "A": {"regex": "foo", "category": "x", "priority": 1},
                "B": {"regex": "bar", "source": "builtin"},
            },
        }
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    patterns = json_utils.load_per_log_patterns_for_file("/var/log/app.log")
    names = {p["name"] for p in patterns}
    assert names == {"A", "B"}
    srcs = {p["source"] for p in patterns}
    assert srcs == {"per_log", "builtin"}
    cat = next(p for p in patterns if p["name"] == "A")
    assert cat["category"] == "x"
    assert cat["priority"] == 1


def test_cache_matches_includes_per_log(monkeypatch):
    app = AppWindow.__new__(AppWindow)
    app.logs = ["foo bar"]
    app.patterns = []
    app.source_path = "/var/log/app.log"

    per_patterns = [
        {"name": "A", "regex": "foo", "source": "per_log", "enabled": True},
        {"name": "B", "regex": "foo bar", "source": "per_log", "enabled": True},
    ]

    import gui.app_window as app_mod

    monkeypatch.setattr(app_mod, "load_per_log_patterns_for_file", lambda p: per_patterns)
    monkeypatch.setattr(app_mod, "get_log_keys_for_file", lambda p: [])

    AppWindow._cache_matches(app)

    names = {m["name"] for m in app.match_cache[1]}
    assert names == {"A", "B"}
    assert app.per_log_patterns == per_patterns

def test_cache_matches_dedupes_duplicates(monkeypatch):
    app = AppWindow.__new__(AppWindow)
    app.logs = ["foo"]
    app.patterns = [{"name": "A", "regex": "foo", "source": "user", "enabled": True}]
    app.source_path = "/var/log/app.log"

    per_patterns = [{"name": "A", "regex": "foo", "source": "per_log", "enabled": True}]

    import gui.app_window as app_mod

    monkeypatch.setattr(app_mod, "load_per_log_patterns_for_file", lambda p: per_patterns)
    monkeypatch.setattr(app_mod, "get_log_keys_for_file", lambda p: [])

    AppWindow._cache_matches(app)

    matches = app.match_cache[1]
    assert len(matches) == 1
    assert matches[0]["source"] == "per_log"


def test_load_per_log_patterns_by_key(tmp_path, monkeypatch):
    file_path = tmp_path / "per.json"
    monkeypatch.setattr(json_utils, "PER_LOG_PATTERNS_PATH", str(file_path))

    data = {
        "app": {
            "file": "/var/log/app.log",
            "patterns": {
                "A": {"regex": "foo"},
                "B": {"pattern": "bar"},
            },
        }
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    pats = json_utils.load_per_log_patterns_by_key("app")
    names = {p["name"] for p in pats}
    assert names == {"A", "B"}
    assert all(p["source"] == "per_log" for p in pats)
    assert all("regex" in p for p in pats)
