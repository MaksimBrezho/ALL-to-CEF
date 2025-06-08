import re
import pytest
from typing import List


from core.regex.enum_generator import EnumRegexGenerator


@pytest.mark.parametrize("words,expected_sample", [
    (["ERROR", "INFO", "DEBUG"], ["ERROR", "INFO", "DEBUG"]),
    (["warn", "warning"], ["warn", "warning"]),
])
def test_basic_generation(words: List[str], expected_sample: List[str]):
    regex = EnumRegexGenerator(words, sort_by_length=True).generate()
    for word in expected_sample:
        assert re.fullmatch(regex, word)


def test_ignore_case():
    gen = EnumRegexGenerator(["one", "Two"], ignore_case=True)
    pattern = gen.generate()
    assert re.fullmatch(pattern, "ONE")
    assert re.fullmatch(pattern, "two")
    assert not re.fullmatch(pattern, "three")


def test_sort_by_length():
    gen = EnumRegexGenerator(["a", "ab", "abc"], sort_by_length=True)
    result = gen.generate()
    assert result.startswith('(?:abc|ab|a)')


def test_group_named():
    gen = EnumRegexGenerator(["on", "off"], group_name="state")
    result = gen.generate()
    match = re.fullmatch(result, "on")
    assert match
    assert match.group("state") == "on"


def test_optional_flag():
    gen = EnumRegexGenerator(["ok"], optional=True)
    pattern = gen.generate()
    assert re.fullmatch(pattern, "ok")
    assert re.fullmatch(pattern, "")  # optional — допускает пустую строку


def test_no_duplicates():
    gen = EnumRegexGenerator(["YES", "YES", "NO", "NO"])
    result = gen.generate()
    words = re.findall(r"[A-Z]+", result)
    assert sorted(set(words)) == ["NO", "YES"]


def test_special_characters_escaped():
    gen = EnumRegexGenerator(["a.b", "a+b", "a*b"])
    pattern = gen.generate()
    assert re.fullmatch(pattern, "a.b")
    assert re.fullmatch(pattern, "a+b")
    assert re.fullmatch(pattern, "a*b")
