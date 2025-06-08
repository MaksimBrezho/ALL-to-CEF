import os
import json
import re


def test_error_code_pattern_matches():
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'patterns_builtin.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    patterns = data.get('patterns', data)
    error_pattern = next(p for p in patterns if p.get('name') == 'Error Code')
    regex = error_pattern.get('regex') or error_pattern.get('pattern')
    assert regex == 'code=\\d{3}'
    assert re.search(regex, 'code=123')
    assert not re.search(regex, 'code=abc')

