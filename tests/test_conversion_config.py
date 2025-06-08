import json
import os

from utils import json_utils, code_generator


def test_conversion_config_roundtrip(monkeypatch, tmp_path):
    conf_file = tmp_path / "conv.json"
    out_dir = tmp_path / "out"
    monkeypatch.setattr(json_utils, "get_conversion_config_path", lambda key=None: str(conf_file))

    patterns = [{"name": "UserPat", "regex": r"user=(\w+)"}]
    monkeypatch.setattr(json_utils, "load_all_patterns", lambda: patterns)

    data = {
        "header": {"CEF Version": "0"},
        "mappings": [
            {"cef": "suser", "pattern": "UserPat", "regex": r"user=(\w+)", "transform": "none"}
        ],
    }

    json_utils.save_conversion_config(data, log_key="app")
    assert conf_file.exists()
    with open(conf_file, "r", encoding="utf-8") as f:
        text = f.read()
        saved = json.loads(text)

    assert "regex" not in text
    assert saved["mappings"][0]["pattern"] == "UserPat"
    assert saved["log_key"] == "app"
    assert "regex" not in saved["mappings"][0]

    loaded = json_utils.load_conversion_config("app")
    assert loaded["mappings"][0]["regex"] == r"user=(\w+)"
    assert loaded["log_key"] == "app"

    paths = code_generator.generate_files(loaded["header"], loaded["mappings"], patterns, out_dir)
    assert any(path.endswith("cef_converter.py") for path in paths)
