import sys
import subprocess
from utils.code_generator import generate_files


def test_generated_main_runs(tmp_path):
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
        'transform': 'none',
    }]

    paths = generate_files(header, mappings, patterns, tmp_path)
    main_path = paths[1]

    with open(tmp_path / 'input.log', 'w', encoding='utf-8') as f:
        f.write('user=john\n')

    subprocess.run([sys.executable, main_path], cwd=tmp_path, check=True)

    assert (tmp_path / 'output.cef').exists()
