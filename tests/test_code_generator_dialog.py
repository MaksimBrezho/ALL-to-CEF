from gui.code_generator_dialog import CodeGeneratorDialog
from utils import json_utils


def test_find_example():
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.logs = ["user=john", "error 42"]
    assert dlg._find_example(r"user=\w+") == "user=john"
    assert dlg._find_example(r"error") == "error"


def test_find_examples():
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.logs = ["user=john", "user=jane", "something else"]
    result = dlg._find_examples(r"user=(\w+)")
    assert result == ["user=john", "user=jane"]


def test_constant_fields_only_when_no_patterns(monkeypatch):
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.per_log_patterns = [
        {"name": "VendorPat", "regex": "foo", "fields": ["deviceVendor"]},
        {"name": "ProductPat", "regex": "bar", "fields": ["deviceProduct"]},
    ]
    monkeypatch.setattr(json_utils, "load_cef_field_keys", lambda: ["deviceVendor", "deviceProduct"])
    monkeypatch.setattr(json_utils, "load_cef_fields", lambda: [{"key": "deviceVendor"}, {"key": "deviceProduct"}])

    mappings = CodeGeneratorDialog._build_initial_mappings(dlg)
    vendor = [m for m in mappings if m["cef"] == "deviceVendor"]
    product = [m for m in mappings if m["cef"] == "deviceProduct"]
    assert vendor[0].get("pattern") == "VendorPat"
    assert product[0].get("pattern") == "ProductPat"


def test_initial_mappings_from_fields(monkeypatch):
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)

    patterns = [
        {"name": "Date L", "regex": "foo", "fields": ["start"]},
        {"name": "Time Range", "regex": "bar", "fields": ["start", "end"]},
    ]

    dlg.per_log_patterns = patterns
    monkeypatch.setattr(CodeGeneratorDialog, "_collect_patterns", lambda self: patterns)
    monkeypatch.setattr(json_utils, "load_cef_field_keys", lambda: ["start", "end"])

    mappings = CodeGeneratorDialog._build_initial_mappings(dlg)
    start = [m["pattern"] for m in mappings if m["cef"] == "start"]
    end = [m["pattern"] for m in mappings if m["cef"] == "end"]

    assert start.count("Date L") == 1
    assert start.count("Time Range") == 1
    assert end == ["Time Range"]


def test_get_transformed_example():
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.logs = ["user=john"]
    result = CodeGeneratorDialog._get_transformed_example(dlg, r"user=\w+", "upper")
    assert result == "USER=JOHN"


def test_get_transformed_example_constant():
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.logs = []
    result = CodeGeneratorDialog._get_transformed_example(dlg, "", "lower", value="ACME")
    assert result == "acme"


def test_initial_mappings_time_transform(monkeypatch):
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)

    patterns = [
        {"name": "TimePat", "regex": "foo", "fields": ["rt"]},
    ]

    dlg.per_log_patterns = patterns
    monkeypatch.setattr(CodeGeneratorDialog, "_collect_patterns", lambda self: patterns)
    monkeypatch.setattr(json_utils, "load_cef_field_keys", lambda: ["rt"])
    monkeypatch.setattr(json_utils, "load_cef_fields", lambda: [{"key": "rt", "category": "Time"}])

    mappings = CodeGeneratorDialog._build_initial_mappings(dlg)
    tran = [m["transform"] for m in mappings if m["cef"] == "rt"]
    assert tran == ["time"]


def test_dialog_merges_new_patterns(monkeypatch):
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.per_log_patterns = [{"name": "NewPat", "regex": "n", "fields": ["deviceVendor"]}]
    dlg.logs = []
    dlg.log_key = "app"

    config = {
        "header": {},
        "mappings": [{"cef": "deviceVendor", "pattern": "OldPat", "transform": "none", "value": ""}],
    }
    monkeypatch.setattr(json_utils, "load_cef_fields", lambda: [{"key": "deviceVendor"}])

    initial = CodeGeneratorDialog._build_initial_mappings(dlg)
    merged = CodeGeneratorDialog._merge_mappings(dlg, config["mappings"], initial)

    patterns = [m.get("pattern") for m in merged if m.get("cef") == "deviceVendor"]
    assert "OldPat" in patterns
    assert "NewPat" in patterns

def test_initial_mappings_signature_id_incremental(monkeypatch):
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.per_log_patterns = []
    monkeypatch.setattr(json_utils, "load_cef_field_keys", lambda: ["signatureID"])
    monkeypatch.setattr(json_utils, "load_cef_fields", lambda: [{"key": "signatureID"}])
    mappings = CodeGeneratorDialog._build_initial_mappings(dlg)
    sig = [m for m in mappings if m["cef"] == "signatureID"][0]
    assert sig.get("rule") == "incremental"


def test_gather_mappings_handles_rule():
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.mappings = [{"cef": "signatureID", "rule": "incremental", "transform": "none"}]
    result = CodeGeneratorDialog._gather_mappings(dlg)
    assert result == [{"cef": "signatureID", "rule": "incremental", "transform": "none"}]


def test_merge_replaces_placeholder(monkeypatch):
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.per_log_patterns = []
    monkeypatch.setattr(json_utils, "load_cef_field_keys", lambda: ["signatureID", "name", "severity"])
    monkeypatch.setattr(json_utils, "load_cef_fields", lambda: [
        {"key": "signatureID"},
        {"key": "name"},
        {"key": "severity"},
    ])

    existing = CodeGeneratorDialog._build_initial_mappings(dlg)

    dlg.per_log_patterns = [
        {"name": "SigPat", "regex": "sig", "fields": ["signatureID"]},
        {"name": "NamePat", "regex": "nm", "fields": ["name"]},
        {"name": "SevPat", "regex": "sv", "fields": ["severity"]},
    ]
    initial = CodeGeneratorDialog._build_initial_mappings(dlg)
    merged = CodeGeneratorDialog._merge_mappings(dlg, existing, initial)

    sig = [m for m in merged if m["cef"] == "signatureID"]
    name = [m for m in merged if m["cef"] == "name"]
    sev = [m for m in merged if m["cef"] == "severity"]

    assert len(sig) == 1 and sig[0].get("pattern") == "SigPat"
    assert len(name) == 1 and name[0].get("pattern") == "NamePat"
    assert len(sev) == 1 and sev[0].get("pattern") == "SevPat"


def test_merge_skips_placeholder_when_constant_exists(monkeypatch):
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.per_log_patterns = []
    monkeypatch.setattr(json_utils, "load_cef_field_keys", lambda: ["deviceVendor"])
    monkeypatch.setattr(json_utils, "load_cef_fields", lambda: [{"key": "deviceVendor"}])

    existing = [{"cef": "deviceVendor", "value": "ACME", "transform": "none"}]
    initial = CodeGeneratorDialog._build_initial_mappings(dlg)
    merged = CodeGeneratorDialog._merge_mappings(dlg, existing, initial)

    vendor = [m for m in merged if m["cef"] == "deviceVendor"]
    assert vendor == existing


def test_save_config_persists_only_version(monkeypatch):
    class DummyVar:
        def __init__(self, val):
            self.val = val
        def get(self):
            return self.val

    captured = {}

    def fake_save(data, key):
        captured['data'] = data
        captured['key'] = key

    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.header_vars = {
        "CEF Version": DummyVar("0"),
        "Device Vendor": DummyVar("ACME"),
    }
    dlg.mappings = []
    dlg.log_key = "app"

    monkeypatch.setattr(json_utils, "save_conversion_config", fake_save)

    CodeGeneratorDialog._save_config(dlg)

    assert captured['data']['header'] == {"CEF Version": "0"}
    assert captured['key'] == "app"
