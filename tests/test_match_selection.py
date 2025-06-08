from core.regex_highlighter import compute_optimal_matches


def test_user_priority_over_builtin():
    line = "abc"
    patterns = [
        {"name": "builtin", "regex": "abc", "priority": 1, "source": "builtin"},
        {"name": "user", "regex": "abc", "priority": 5, "source": "user"},
    ]
    result = compute_optimal_matches(line, patterns)
    assert len(result) == 1
    assert result[0]["name"] == "user"


def test_tie_breaker_prefers_longer():
    line = "abcdef"
    patterns = [
        {"name": "short", "regex": "abc", "priority": 1, "source": "builtin"},
        {"name": "long", "regex": "abcdef", "priority": 1, "source": "builtin"},
    ]
    result = compute_optimal_matches(line, patterns)
    assert len(result) == 1
    assert result[0]["name"] == "long"
