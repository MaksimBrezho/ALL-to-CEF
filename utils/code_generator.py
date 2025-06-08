"""Generate CEF converter class and helper script."""

from __future__ import annotations

import os
from textwrap import dedent
from typing import List, Dict
import json

from .transform_logic import apply_transform


def generate_files(
    header: Dict[str, str],
    mappings: List[Dict],
    patterns: List[Dict],
    output_dir: str,
    log_name: str | None = None,
) -> list[str]:
    """Generate converter and main script files.

    Parameters
    ----------
    header : dict
        Values for CEF header fields.
    mappings : list of dict
        Mapping definitions. Supported keys:
        - 'cef': target CEF field name
        - 'pattern': source pattern name
        - 'group': capture group number (optional)
        - 'groups': list of capture groups to combine (optional)
        - 'transform': transformation definition
        - 'value': constant value if no pattern
        - 'value_map': mapping of values
        - 'replace_pattern': regex for replacement check
        - 'replace_with': replacement value
        - 'rule': special rule like 'incremental'
    patterns : list of dict
        Available patterns with 'name' and 'regex'.
    output_dir : str
        Directory to write generated files.
    log_name : str, optional
        Optional log identifier used in generated file names and comments.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Filter provided patterns to only those referenced in mappings
    used_names = set()
    for m in mappings:
        p = m.get("pattern")
        if isinstance(p, dict):
            name = p.get("name")
        else:
            name = p
        if name:
            used_names.add(name)

    if used_names:
        patterns = [p for p in patterns if p.get("name") in used_names]

    suffix = f"_{log_name}" if log_name else ""
    converter_path = os.path.join(output_dir, f"cef_converter{suffix}.py")
    main_path = os.path.join(output_dir, f"main_cef_converter{suffix}.py")

    # Override header values with constants from mappings when available
    header_map = {
        "Device Vendor": "deviceVendor",
        "Device Product": "deviceProduct",
        "Device Version": "deviceVersion",
        "Event Class ID": "signatureID",
        "Event Name": "name",
        "Severity (int)": "severity",
    }
    updated_header = dict(header)
    for key, cef_key in header_map.items():
        for m in mappings:
            if m.get("cef") == cef_key and m.get("value") and not m.get("pattern"):
                updated_header[key] = apply_transform(m["value"], m.get("transform", "none"))
                break

    header_repr = json.dumps(updated_header, ensure_ascii=False, indent=4)
    pattern_entries = []
    for p in patterns:
        key = json.dumps(p['name'], ensure_ascii=False)
        pattern_entries.append(f"    {key}: re.compile(r'''{p['regex']}''')")
    pattern_repr = "{\n" + ",\n".join(pattern_entries) + "\n}"
    mapping_repr = "[\n" + ",\n".join(
        "    " + repr(m) for m in mappings
    ) + "\n]"

    comment = f"# Converter for log: {log_name}" if log_name else "# Converter"

    converter_code = f"""
{comment}
import re
from datetime import timezone
from dateutil import parser as date_parser
from typing import Any, Dict, List


def _normalize_time(value: str) -> str:
    '''Parse an arbitrary date string and return ISO-8601 in UTC.'''
    if not value:
        return value
    try:
        if '/' in value:
            dt = date_parser.parse(value, dayfirst=True)
        else:
            dt = date_parser.parse(value)
    except (ValueError, TypeError):
        return value
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _apply_basic_transform(value: str, transform: str) -> str:
    '''Apply a basic string transformation.'''
    if value is None:
        value = ""
    if transform == "lower":
        return value.lower()
    if transform == "upper":
        return value.upper()
    if transform == "capitalize":
        return value.title()
    if transform == "sentence":
        return value[:1].upper() + value[1:].lower() if value else value
    if transform == "time":
        return _normalize_time(value)
    return value


def _reorder_tokens(value: str, regex: str, order: List[int]) -> str:
    '''Reorder regex-derived tokens according to the provided order.'''
    try:
        pat = re.compile(regex)
    except re.error:
        return value
    m = pat.search(value or "")
    if not m:
        return value
    tokens: List[str] = []
    if m.lastindex:
        pos = m.start()
        for i in range(1, (m.lastindex or 0) + 1):
            literal = value[pos:m.start(i)]
            if literal:
                tokens.append(literal)
            tokens.append(m.group(i))
            pos = m.end(i)
        tail = value[pos:m.end()]
        if tail:
            tokens.append(tail)
    else:
        span = value[m.start():m.end()]
        tokens = [t for t in re.split(r"([a-zA-Z]+|\\d+|\\W)", span) if t]
    return "".join(tokens[i] for i in order if i < len(tokens))


def apply_transform(value: str, transform: Any) -> str:
    '''Apply a basic or advanced transformation.'''
    if isinstance(transform, dict):
        fmt = transform.get("format", "none")
        if transform.get("token_order") and transform.get("regex"):
            order = [int(i) for i in transform.get("token_order", [])]
            value = _reorder_tokens(value, transform["regex"], order)
        if transform.get("replace_pattern"):
            pat = re.compile(transform["replace_pattern"])
            if pat.fullmatch(value or ""):
                value = transform.get("replace_with", "")
        if transform.get("value_map"):
            mapping: Dict[str, str] = transform["value_map"]
            if value in mapping:
                value = mapping[value]
            else:
                for k, v in mapping.items():
                    if k in (value or ""):
                        value = (value or "").replace(k, v)
        return _apply_basic_transform(value, fmt)
    return _apply_basic_transform(value, str(transform))


class LogToCEFConverter:
    def __init__(self):
        self.compiled_patterns = {pattern_repr}
        self.mappings = {mapping_repr}
        self.cef_header = {header_repr}
        self._sig_counter = -1

    def convert_line(self, line: str) -> str:
        matches = {{name: rgx.search(line) for name, rgx in self.compiled_patterns.items()}}
        fields = {{}}
        for m in self.mappings:
            if m.get('rule') == 'incremental':
                self._sig_counter += 1
                value = str(self._sig_counter)
            elif m.get('pattern'):
                match = matches.get(m['pattern'])
                if match:
                    if 'groups' in m:
                        parts = [match.group(g) for g in m['groups']]
                        value = ' '.join(parts)
                    else:
                        value = match.group(m.get('group', 0))
                else:
                    value = ''
            else:
                value = m.get('value', '')

            if m.get('replace_pattern'):
                if re.fullmatch(m['replace_pattern'], value):
                    value = m.get('replace_with', '')
            if m.get('value_map'):
                mapping = m['value_map']
                if value in mapping:
                    value = mapping[value]
                else:
                    for k, v in mapping.items():
                        if k in value:
                            value = value.replace(k, v)

            fields[m['cef']] = apply_transform(value, m.get('transform', 'none'))
        return self._build_cef_string(fields)

    def _build_cef_string(self, fields: dict) -> str:
        h = self.cef_header
        head = f"CEF:{{h.get('CEF Version')}}|{{h.get('Device Vendor')}}|{{h.get('Device Product')}}|{{h.get('Device Version')}}|{{h.get('Event Class ID')}}|{{h.get('Event Name')}}|{{h.get('Severity (int)')}}"
        ext = ' '.join(f"{{k}}={{v}}" for k, v in fields.items() if v)
        return head + '|' + ext

    def coverage_score(self, line: str) -> float:
        matches = [rgx.search(line) for rgx in self.compiled_patterns.values()]
        covered = sum(len(m.group(0)) for m in matches if m)
        significant = ''.join(ch for ch in line if ch.isalnum())
        return 100.0 if not significant else covered / len(significant) * 100

    def log_incomplete_coverage(self, line: str, coverage: float, fp):
        fp.write(f"{{line}} | coverage={{coverage:.1f}}%\\n")
"""

    comment_main = f"# Runner for log: {log_name}" if log_name else "# Runner"
    main_code = dedent(
        f"""
{comment_main}
from cef_converter{suffix} import LogToCEFConverter

def main():
    conv = LogToCEFConverter()
    with open('input.log', 'r', encoding='utf-8') as fin, \
         open('output.cef', 'w', encoding='utf-8') as fout, \
         open('error.log', 'w', encoding='utf-8') as ferr:
        for line in fin:
            line = line.rstrip('\\n')
            cef = conv.convert_line(line)
            fout.write(cef + '\\n')
            cov = conv.coverage_score(line)
            if cov < 100.0:
                conv.log_incomplete_coverage(line, cov, ferr)

if __name__ == '__main__':
    main()
"""
    ).lstrip()

    with open(converter_path, 'w', encoding='utf-8') as f:
        f.write(converter_code)
    with open(main_path, 'w', encoding='utf-8') as f:
        f.write(main_code)

    return [converter_path, main_path]


