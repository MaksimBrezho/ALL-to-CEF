from typing import List, Dict

from utils.text_utils import compute_char_coverage


def test_compute_char_coverage():
    logs = [
        "error 123",
        "abc 456",
        "def"
    ]
    match_cache: Dict[int, List[Dict]] = {
        1: [
            {"name": "p1", "match": "error 123"}
        ],
        2: [
            {"name": "p2", "match": "abc"}
        ],
        3: []
    }
    active_names = {"p1", "p2"}
    coverage = compute_char_coverage(logs, match_cache, active_names)
    assert round(coverage, 1) == round(11 / 17 * 100, 1)


def test_coverage_no_double_count():
    logs = ["abcdef"]
    match_cache = {
        1: [
            {"name": "p1", "match": "abc", "start": 0, "end": 3},
            {"name": "p2", "match": "cde", "start": 2, "end": 5},
        ]
    }
    coverage = compute_char_coverage(logs, match_cache, {"p1", "p2"})
    assert round(coverage, 1) == round(5 / 6 * 100, 1)
