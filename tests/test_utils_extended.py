import json
import re
import math
import tempfile


from utils import json_utils, color_utils, text_utils
from core.tokenizer.tree_tokenizer import build_token_tree, flatten_token_tree
from core.regex.regex_builder import _merge_tokens_regex, build_draft_regex_from_examples


def test_common_prefix_suffix_and_significant_chars():
    assert text_utils.common_prefix(["flower", "flow", "flight"]) == "fl"
    assert text_utils.common_suffix(["testing", "ping", "king"]) == "ing"
    assert text_utils.count_significant_chars(" a b \n c ") == 3


def test_color_utils_roundtrip_and_generation():
    rgb = color_utils.hex_to_rgb("#ff00ff")
    assert rgb == (1.0, 0.0, 1.0)
    assert color_utils.rgb_to_hex(rgb) == "#ff00ff"
    shade = color_utils.get_shaded_color("#808080", 0, 3)
    assert re.fullmatch(r"#[0-9a-f]{6}", shade)
    colors = color_utils.generate_distinct_colors(5)
    assert len(colors) == 5
    assert len(set(colors)) == 5
    assert all(re.fullmatch(r"#[0-9a-f]{6}", c) for c in colors)


def test_adjust_lightness_roundtrip():
    lighter = color_utils.adjust_lightness("#808080", 1.5)
    darker = color_utils.adjust_lightness("#808080", 0.5)
    assert re.fullmatch(r"#[0-9a-f]{6}", lighter)
    assert re.fullmatch(r"#[0-9a-f]{6}", darker)
    # lighter color should have larger lightness than darker one
    l_light = color_utils.hex_to_rgb(lighter)[0]  # r channel approximates lightness order
    l_dark = color_utils.hex_to_rgb(darker)[0]
    assert l_light > l_dark


def test_json_utils_load_and_save_user_patterns(tmp_path, monkeypatch):
    user_file = tmp_path / "user.json"
    builtin_file = tmp_path / "builtin.json"
    monkeypatch.setattr(json_utils, "USER_PATTERNS_PATH", str(user_file))
    monkeypatch.setattr(json_utils, "BUILTIN_PATTERNS_PATH", str(builtin_file))

    with open(user_file, "w", encoding="utf-8") as f:
        json.dump({"patterns": [{"name": "p1", "regex": "a"}]}, f)
    with open(builtin_file, "w", encoding="utf-8") as f:
        json.dump({"patterns": [{"name": "p2", "pattern": "b"}]}, f)

    patterns = json_utils.load_all_patterns()
    names = {p["name"] for p in patterns}
    assert names == {"p1", "p2"}
    assert all("regex" in p for p in patterns)
    assert {p["source"] for p in patterns} == {"user", "builtin"}

    new_patterns = [{"name": "x", "regex": "z"}]
    json_utils.save_user_patterns(new_patterns)
    with open(user_file, "r", encoding="utf-8") as f:
        saved = json.load(f)
    assert saved == {"patterns": new_patterns}

    # save_user_pattern should replace old entry with same name
    json_utils.save_user_pattern({"name": "x", "regex": "q"})
    with open(user_file, "r", encoding="utf-8") as f:
        saved = json.load(f)["patterns"]
    assert saved == [{"name": "x", "regex": "q"}]


def test_json_utils_cef_fields(tmp_path, monkeypatch):
    cef_file = tmp_path / "cef.json"
    monkeypatch.setattr(json_utils, "CEF_FIELDS_PATH", str(cef_file))
    with open(cef_file, "w", encoding="utf-8") as f:
        json.dump({"fields": [{"key": "rt"}, {"key": "start"}]}, f)
    assert json_utils.load_cef_field_keys() == ["rt", "start"]


def test_tokenizer_group_parsing():
    tree = build_token_tree('echo "hello world" (a,b)')
    flat = flatten_token_tree(tree)
    assert flat == [
        ('echo', 'token'),
        (' ', 'sep'),
        ('hello', 'token'),
        (' ', 'sep'),
        ('world', 'token'),
        (' ', 'sep'),
        ('a', 'token'),
        (',', 'sep'),
        ('b', 'token')
    ]


def test_merge_tokens_regex_optional_segment():
    pattern = _merge_tokens_regex([['A', 'X', 'B'], ['A', 'B']], case_insensitive=False)
    assert re.fullmatch(pattern, 'A X B')
    assert re.fullmatch(pattern, 'A B')
    assert not re.fullmatch(pattern, 'A Y B')


def test_digit_mode_always_fixed_length():
    lines = ['id=12', 'id=34']
    regex = build_draft_regex_from_examples(lines, digit_mode='always_fixed_length')
    assert re.fullmatch(regex, 'id=99')
    assert not re.fullmatch(regex, 'id=9')


def test_line_number_ranges():
    assert text_utils.line_number_ranges([]) == ""
    assert text_utils.line_number_ranges([2]) == "2"
    assert text_utils.line_number_ranges([1, 2, 3, 5, 7, 8, 9]) == "1-3, 5, 7-9"
    assert text_utils.line_number_ranges([5, 4, 3, 3, 2]) == "2-5"


