from utils.transform_logic import apply_transform


def test_apply_transform_modes():
    assert apply_transform('TeSt', 'lower') == 'test'
    assert apply_transform('TeSt', 'upper') == 'TEST'
    assert apply_transform('hello world', 'capitalize') == 'Hello World'
    assert apply_transform('hello WORLD', 'sentence') == 'Hello world'
    assert apply_transform('Same', 'none') == 'Same'


def test_apply_transform_dict_map():
    spec = {
        'format': 'upper',
        'value_map': {'info': '1', 'error': '8'},
    }
    assert apply_transform('info', spec) == '1'
    assert apply_transform('error', spec) == '8'


def test_apply_transform_dict_map_substring():
    spec = {
        'format': 'none',
        'value_map': {'ERROR': '1', 'WARN': '2'},
    }
    assert apply_transform('Info: ERROR', spec) == 'Info: 1'
    assert apply_transform('Detail WARN here', spec) == 'Detail 2 here'


def test_apply_transform_dict_replace():
    spec = {
        'format': 'none',
        'replace_pattern': r'foo',
        'replace_with': 'BAR'
    }
    assert apply_transform('foo', spec) == 'BAR'
    assert apply_transform('baz', spec) == 'baz'


def test_apply_transform_token_order():
    spec = {
        'format': 'none',
        'regex': r'(\w+) (\w+) (\d+)',
        'token_order': [2, 1, 0, 3, 4]
    }
    assert apply_transform('foo bar 123', spec) == 'bar foo 123'


def test_reorder_tokens_no_groups():
    spec = {
        'format': 'none',
        'regex': r'\d{2}/\d{2}/\d{4}',
        'token_order': [4, 3, 2, 1, 0]
    }
    assert apply_transform('01/02/2024', spec) == '2024/02/01'


def test_apply_transform_complex_reorder():
    spec = {
        'format': 'none',
        'regex': r'[a-zA-Z]+ {1,2}\d{1,2}\ \d{2}:\d{2}:\d{2}',
        'token_order': [2, 3, 4, 5, 6, 7, 8, 1, 0]
    }
    examples = [
        'Jun 14 15:16:01',
        'Jun 14 15:16:02',
        'Jun 15 02:04:59',
        'Jun 15 04:06:18',
        'Jun 15 04:06:19',
    ]
    results = [apply_transform(e, spec) for e in examples]
    assert results == [
        '14 15:16:01 Jun',
        '14 15:16:02 Jun',
        '15 02:04:59 Jun',
        '15 04:06:18 Jun',
        '15 04:06:19 Jun',
    ]


def test_apply_transform_lookahead_reorder():
    spec = {
        'format': 'none',
        'regex': r'[a-zA-Z]+ {1,2}\d{1,2}\ \d{2}:\d{2}:\d{2}(?= combo)',
        'token_order': [2, 3, 4, 5, 6, 7, 8, 1, 0],
    }
    examples = [
        'Jun 14 15:16:01 combo',
        'Jun 14 15:16:02 combo',
        'Jun 15 02:04:59 combo',
        'Jun 15 04:06:18 combo',
        'Jun 15 04:06:19 combo',
    ]
    results = [apply_transform(e, spec) for e in examples]
    assert results == [
        '14 15:16:01 Jun',
        '14 15:16:02 Jun',
        '15 02:04:59 Jun',
        '15 04:06:18 Jun',
        '15 04:06:19 Jun',
    ]


def test_apply_transform_time_iso():
    assert apply_transform('2024-06-02T12:34:56Z', 'time') == '2024-06-02T12:34:56Z'


def test_apply_transform_time_space():
    assert apply_transform('2024-06-02 12:34:56', 'time') == '2024-06-02T12:34:56Z'


def test_apply_transform_time_various_formats():
    assert apply_transform('Jun 02, 2024 12:34:56', 'time') == '2024-06-02T12:34:56Z'
    assert apply_transform('02/06/2024 12:34:56 +0300', 'time') == '2024-06-02T09:34:56Z'
