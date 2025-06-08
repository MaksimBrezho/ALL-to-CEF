import json


from utils import json_utils


def test_save_and_get_log_keys(monkeypatch, tmp_path):
    mapping_file = tmp_path / "map.json"
    monkeypatch.setattr(json_utils, "LOG_KEY_MAP_PATH", str(mapping_file))

    json_utils.save_log_key_mapping("/var/log/app.log", ["app"], log_name="app")
    assert mapping_file.exists()
    with open(mapping_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["app"]["file"] == "/var/log/app.log"
    assert data["app"]["keys"] == ["app"]

    json_utils.save_log_key_mapping("/var/log/other.log", ["other"])
    with open(mapping_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "other.log" in data
    assert data["other.log"]["keys"] == ["other"]

    assert json_utils.get_log_keys_for_file("/var/log/app.log") == ["app"]
    assert json_utils.get_log_keys_for_file("/var/log/other.log") == ["other"]
    assert json_utils.get_log_keys_for_file("/missing.log") == []
