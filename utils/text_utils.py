import re
from typing import List, Dict


def common_prefix(words):
    if not words:
        return ''
    prefix = words[0]
    for w in words[1:]:
        i = 0
        max_i = min(len(prefix), len(w))
        while i < max_i and prefix[i] == w[i]:
            i += 1
        prefix = prefix[:i]
        if not prefix:
            break
    return prefix


def common_suffix(words):
    if not words:
        return ''
    suffix = words[0]
    for w in words[1:]:
        i = 0
        max_i = min(len(suffix), len(w))
        while i < max_i and suffix[-1 - i] == w[-1 - i]:
            i += 1
        suffix = suffix[len(suffix)-i:]
        if not suffix:
            break
    return suffix


def count_significant_chars(text: str) -> int:
    """Return the length of text excluding any whitespace characters."""
    return len("".join(ch for ch in text if not ch.isspace()))


def line_number_ranges(nums: List[int]) -> str:
    """Return comma-separated line number ranges.

    Consecutive numbers are collapsed into ``start-end`` form.
    """
    if not nums:
        return ""
    nums = sorted(set(nums))
    ranges = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
        else:
            ranges.append(f"{start}-{prev}" if start != prev else str(start))
            start = prev = n
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return ", ".join(ranges)


def compute_char_coverage(
    logs: List[str], matches_by_line: Dict[int, List[Dict]], active_names: set
) -> float:
    """Calculate coverage by number of significant characters.

    Parameters
    ----------
    logs : List[str]
        Source log lines.
    matches_by_line : Dict[int, List[Dict]]
        Mapping of line number to list of match dictionaries.
    active_names : set
        Names of patterns that should be counted in coverage.

    Returns
    -------
    float
        Coverage percentage from 0 to 100.
    """
    total = sum(count_significant_chars(line) for line in logs)
    if total == 0:
        return 0.0

    covered = 0
    for lineno, matches in matches_by_line.items():
        ranges = []
        for m in matches:
            if m.get("name") not in active_names:
                continue
            start = m.get("start")
            end = m.get("end")
            if start is None or end is None:
                start = 0
                end = len(m.get("match", ""))
            ranges.append((start, end))

        if not ranges:
            continue

        ranges.sort()
        merged = [list(ranges[0])]
        for start, end in ranges[1:]:
            last = merged[-1]
            if start <= last[1]:
                last[1] = max(last[1], end)
            else:
                merged.append([start, end])

        line_text = logs[lineno - 1] if 0 < lineno <= len(logs) else ""
        for start, end in merged:
            segment = line_text[start:end]
            covered += count_significant_chars(segment)

    return covered / total * 100



def compute_field_line_stats(
    logs: List[str],
    matches_by_line: Dict[int, List[Dict]],
    active_names: set,
    pattern_fields: Dict[str, List[str]],
    fields: List[str] | None = None,
) -> Dict[str, tuple[float, list[int]]]:
    """Return coverage stats per line for specified fields.

    Parameters
    ----------
    logs : list[str]
        Log lines to analyze.
    matches_by_line : dict
        Mapping of line number to pattern match dictionaries.
    active_names : set
        Names of patterns that are currently enabled.
    pattern_fields : dict
        Mapping of pattern name to list of CEF fields.
    fields : list[str] | None
        Target CEF fields to check. Defaults to common fields.

    Returns
    -------
    dict
        Mapping field -> (percent_with_field, missing_line_numbers)
    """
    if fields is None:
        fields = ["name", "severity", "msg", "signatureID"]

    total_lines = len(logs)
    stats = {f: [0, []] for f in fields}  # count, missing lines

    for i, _ in enumerate(logs, start=1):
        line_matches = matches_by_line.get(i, [])
        present = {f: False for f in fields}
        for m in line_matches:
            if m.get("name") not in active_names:
                continue
            name = m.get("name")
            fields_for_pat = pattern_fields.get(name, [])
            for f in fields:
                if f in fields_for_pat or name == f:
                    present[f] = True
        for f in fields:
            if present[f]:
                stats[f][0] += 1
            else:
                stats[f][1].append(i)

    result = {}
    for f, (count, missing) in stats.items():
        percent = 0.0 if total_lines == 0 else count / total_lines * 100
        result[f] = (percent, missing)
    return result

