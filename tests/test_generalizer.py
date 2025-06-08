import re
import pytest

from core.regex.generalizer import generalize_token


@pytest.mark.parametrize("token,expected_pattern,input_str,should_match", [
    # Числа с фиксированной длиной
    ("123", r"\d{3}", "123", True),
    ("5", r"\d{1}", "5", True),

    # Длинные числа — \d+
    ("12345", r"\d+", "67890", True),

    # Буквы
    ("abc", r"[a-zA-Z]+", "XYZ", True),
    ("Test", r"[a-zA-Z]+", "testCASE", True),

    # Слова с дефисами/подчёркиванием
    ("hello-world", r"[\w\-]+", "word_123-name", True),

    # Комбинированные слова
    ("word123", r"\w+", "abc_99", True),

    # Спецсимволы — должны экранироваться
    ("a+b", r"a\+b", "a+b", True),
    ("{ok}", r"\{ok\}", "{ok}", True),

    # Неверное сопоставление
    ("123", r"\d{3}", "abc", False),
])
def test_generalize_token(token, expected_pattern, input_str, should_match):
    pattern = generalize_token(token)
    assert pattern == expected_pattern
    match = re.fullmatch(pattern, input_str)
    assert (match is not None) == should_match
