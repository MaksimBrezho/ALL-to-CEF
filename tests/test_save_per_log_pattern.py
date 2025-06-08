import json


from utils import json_utils


def test_save_per_log_pattern_creates_files(monkeypatch, tmp_path):
    per_file = tmp_path / "per_log.json"
    map_file = tmp_path / "map.json"
    monkeypatch.setattr(json_utils, "PER_LOG_PATTERNS_PATH", str(per_file))
    monkeypatch.setattr(json_utils, "LOG_KEY_MAP_PATH", str(map_file))

    pat = {"regex": "a", "category": "C", "source": "builtin", "priority": 5}
    json_utils.save_per_log_pattern("/var/log/app.log", "p1", pat, log_name="app")

    assert per_file.exists()
    assert map_file.exists()

    with open(per_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "app" in data
    assert data["app"]["file"] == "/var/log/app.log"
    assert "p1" in data["app"]["patterns"]
    saved = data["app"]["patterns"]["p1"]
    assert saved["category"] == "C"
    assert saved["source"] == "per_log"
    assert saved["priority"] == 5

    with open(map_file, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    assert mapping["app"]["file"] == "/var/log/app.log"

    assert json_utils.get_log_name_for_file("/var/log/app.log") == "app"

    loaded = json_utils.load_per_log_patterns_for_file("/var/log/app.log")
    p = next(p for p in loaded if p["name"] == "p1")
    assert p["category"] == "C"
    assert p["source"] == "per_log"
    assert p["priority"] == 5
