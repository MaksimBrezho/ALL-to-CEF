import os
import importlib.util

from utils.code_generator import generate_files


def test_generate_files_and_converter(tmp_path):
    header = {
        'CEF Version': '0',
        'Device Vendor': 'ACME',
        'Device Product': 'LP',
        'Device Version': '1.0',
        'Event Class ID': '42',
        'Event Name': 'Test',
        'Severity (int)': '5',
    }
    patterns = [{
        'name': 'UserName',
        'regex': r'user=(\w+)',
    }]
    mappings = [{
        'cef': 'suser',
        'pattern': 'UserName',
        'group': 1,
        'transform': 'upper',
    }]

    paths = generate_files(header, mappings, patterns, tmp_path)
    conv_path = os.path.join(tmp_path, 'cef_converter.py')
    assert conv_path in paths

    spec = importlib.util.spec_from_file_location('cef_converter', conv_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    conv = module.LogToCEFConverter()
    result = conv.convert_line('user=john')
    assert 'ACME' in result and 'JOHN' in result


def test_generate_files_constant_value(tmp_path):
    header = {'CEF Version': '0'}
    patterns = []
    mappings = [{
        'cef': 'deviceVendor',
        'value': 'ACME',
        'transform': 'none',
    }]

    paths = generate_files(header, mappings, patterns, tmp_path)
    spec = importlib.util.spec_from_file_location('cef_converter', paths[0])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    conv = module.LogToCEFConverter()
    result = conv.convert_line('line')
    assert 'deviceVendor=ACME' in result


def test_generate_files_advanced(tmp_path):
    header = {
        'CEF Version': '0',
        'Device Vendor': 'ACME',
        'Device Product': 'LP',
        'Device Version': '1.0',
        'Event Class ID': '42',
        'Event Name': 'Test',
        'Severity (int)': '5',
    }
    patterns = [
        {'name': 'FullName', 'regex': r'full=(\w+) (\w+)'},
        {'name': 'Severity', 'regex': r'sev=(\w+)'},
        {'name': 'Status', 'regex': r'status=(\w+)'},
    ]
    mappings = [
        {
            'cef': 'suser',
            'pattern': 'FullName',
            'groups': [1, 2],
            'transform': 'upper',
        },
        {
            'cef': 'severity',
            'pattern': 'Severity',
            'group': 1,
            'value_map': {'info': '1', 'error': '8'},
            'transform': 'none',
        },
        {
            'cef': 'app',
            'pattern': 'Status',
            'group': 1,
            'replace_pattern': r'unknown',
            'replace_with': 'UNKNOWN',
            'transform': 'none',
        },
    ]

    paths = generate_files(header, mappings, patterns, tmp_path)
    spec = importlib.util.spec_from_file_location('cef_converter', paths[0])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    conv = module.LogToCEFConverter()
    line = 'full=john doe sev=error status=unknown'
    result = conv.convert_line(line)
    assert 'suser=JOHN DOE' in result
    assert 'severity=8' in result
    assert 'app=UNKNOWN' in result


def test_generate_files_value_map_substring(tmp_path):
    header = {'CEF Version': '0'}
    patterns = [
        {'name': 'Msg', 'regex': r'msg=(.*)'}
    ]
    mappings = [
        {
            'cef': 'msg',
            'pattern': 'Msg',
            'group': 1,
            'value_map': {'ERROR': '1', 'WARN': '2'},
            'transform': 'none',
        },
    ]

    paths = generate_files(header, mappings, patterns, tmp_path)
    spec = importlib.util.spec_from_file_location('cef_converter', paths[0])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    conv = module.LogToCEFConverter()
    line = 'msg=Info: ERROR and more'
    result = conv.convert_line(line)
    assert 'msg=Info: 1 and more' in result


def test_generate_files_incremental_rule(tmp_path):
    header = {'CEF Version': '0'}
    patterns = []
    mappings = [
        {
            'cef': 'signatureID',
            'rule': 'incremental',
            'transform': 'none',
        },
    ]

    paths = generate_files(header, mappings, patterns, tmp_path)
    spec = importlib.util.spec_from_file_location('cef_converter', paths[0])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    conv = module.LogToCEFConverter()
    r1 = conv.convert_line('l1')
    r2 = conv.convert_line('l2')
    r3 = conv.convert_line('l3')
    assert 'signatureID=0' in r1
    assert 'signatureID=1' in r2
    assert 'signatureID=2' in r3


def test_generate_files_handles_quotes(tmp_path):
    header = {'CEF Version': '0'}
    patterns = [
        {'name': "Int'l Phone Format", 'regex': r'foo'}
    ]
    mappings = [
        {
            'cef': 'dvc',
            'pattern': "Int'l Phone Format",
            'transform': 'none',
        }
    ]

    paths = generate_files(header, mappings, patterns, tmp_path, log_name='test')
    spec = importlib.util.spec_from_file_location('cef_converter', paths[0])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    conv = module.LogToCEFConverter()
    result = conv.convert_line('foo')
    assert 'dvc=foo' in result


def test_generate_files_filters_unused_patterns(tmp_path):
    header = {'CEF Version': '0'}
    patterns = [
        {'name': 'Used', 'regex': r'us'},
        {'name': 'Unused', 'regex': r'un'},
    ]
    mappings = [
        {
            'cef': 'msg',
            'pattern': 'Used',
            'transform': 'none',
        }
    ]
    paths = generate_files(header, mappings, patterns, tmp_path)
    spec = importlib.util.spec_from_file_location('cef_converter', paths[0])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    conv = module.LogToCEFConverter()
    assert set(conv.compiled_patterns.keys()) == {'Used'}


