import re
from typing import List, Dict


# GUI and color utilities are imported lazily inside ``apply_highlighting`` so
# that ``compute_optimal_matches`` can be used without requiring tkinter or
# matplotlib at import time.



def compute_optimal_matches(
    line: str, patterns: List[Dict], log_keys: List[str] | None = None
) -> List[Dict]:
    """Return list of pattern matches following priority rules."""

    log_keys = set(log_keys or [])

    keyed = []
    user = []
    builtin = []
    for pat in patterns:
        src = pat.get("source")
        p_keys = set(pat.get("log_keys") or [])
        has_key = bool(p_keys & log_keys)
        if src in {"per_log", "log"}:
            keyed.append(pat)
        elif src == "user":
            if has_key:
                keyed.append(pat)
            else:
                user.append(pat)
        else:
            if has_key:
                keyed.append(pat)
            else:
                builtin.append(pat)


    def _collect(pats, blocked=None):
        blocked = blocked or []

        def overlaps(start: int, end: int) -> bool:
            for s, e in blocked:
                if start < e and end > s:
                    return True
            return False

        collected = []
        for pat in pats:
            regex = pat.get("regex") or pat.get("pattern")
            try:
                compiled = re.compile(regex)
            except re.error:
                continue
            for m in compiled.finditer(line):
                if overlaps(m.start(), m.end()):
                    continue
                collected.append({
                    "start": m.start(),
                    "end": m.end(),
                    "length": m.end() - m.start(),
                    "match": m.group(),
                    "category": pat.get("category", "Unknown"),
                    "name": pat.get("name", "Unnamed"),
                    "source": pat.get("source", "unknown"),
                    "regex": regex,
                    "priority": pat.get("priority", 1),
                })
        return collected

    def _wis(items):
        """Weighted interval scheduling with deterministic tie breaking."""
        if not items:
            return []

        items.sort(key=lambda m: m["end"])
        n = len(items)
        dp_weight = [0] * n
        dp_length = [0] * n
        prev = [-1] * n

        def find_last_non_conflicting(i):
            for j in range(i - 1, -1, -1):
                if items[j]["end"] <= items[i]["start"]:
                    return j
            return -1

        for i in range(n):
            incl_w = items[i]["priority"]
            incl_len = items[i]["length"]
            j = find_last_non_conflicting(i)
            if j != -1:
                incl_w += dp_weight[j]
                incl_len += dp_length[j]
            excl_w = dp_weight[i - 1] if i > 0 else 0
            excl_len = dp_length[i - 1] if i > 0 else 0

            if (
                incl_w > excl_w
                or (incl_w == excl_w and incl_len > excl_len)
            ):
                dp_weight[i] = incl_w
                dp_length[i] = incl_len
                prev[i] = j
            else:
                dp_weight[i] = excl_w
                dp_length[i] = excl_len
                prev[i] = -2  # special marker: skip this match

        result = []
        i = n - 1
        while i >= 0:
            if prev[i] == -2:
                i -= 1
            else:
                result.append(items[i])
                i = prev[i]
        return list(reversed(result))

    keyed_matches = _collect(keyed)

    intervals = [(m["start"], m["end"]) for m in keyed_matches]

    user_raw = _collect(user, intervals)
    user_matches = _wis(user_raw)
    intervals.extend((m["start"], m["end"]) for m in user_matches)

    builtin_raw = _collect(builtin, intervals)
    builtin_matches = _wis(builtin_raw)

    all_matches = keyed_matches + user_matches + builtin_matches

    all_matches.sort(key=lambda m: m["start"])

    for i in range(len(all_matches)):
        for j in range(i + 1, len(all_matches)):
            if all_matches[i]["end"] > all_matches[j]["start"] and all_matches[j]["end"] > all_matches[i]["start"]:
                all_matches[i]["overlap"] = True
                all_matches[j]["overlap"] = True

    return all_matches


def find_matches_in_line(
    line: str, patterns: List[Dict], log_keys: List[str] | None = None
) -> List[Dict]:
    """Convenience wrapper around :func:`compute_optimal_matches`."""
    return compute_optimal_matches(line, patterns, log_keys)


def apply_highlighting(
    text_widget,
    matches_by_line: Dict[int, List[Dict]],
    active_names: set,
    color_map: Dict[str, str],
    tag_map: Dict[str, Dict] | None = None,
):
    # Import GUI and color utilities lazily to avoid unnecessary dependencies
    # when this module is used purely for match computation in tests.
    import tkinter as tk
    from utils.color_utils import get_shaded_color, adjust_lightness

    for tag in text_widget.tag_names():
        text_widget.tag_remove(tag, "1.0", tk.END)
        try:
            text_widget.tag_delete(tag)
        except tk.TclError:
            pass

    if tag_map is not None:
        tag_map.clear()

    pattern_keys = []
    seen = set()
    for matches in matches_by_line.values():
        for m in matches:
            key = (m["category"], m["regex"])
            if key not in seen:
                pattern_keys.append(key)
                seen.add(key)

    pattern_index_map = {key: i for i, key in enumerate(pattern_keys)}
    total = len(pattern_keys) or 1

    for lineno, matches in matches_by_line.items():
        for m in matches:
            if m["name"] not in active_names:
                continue

            key = (m["category"], m["regex"])
            idx = pattern_index_map.get(key, 0)
            base_color = color_map.get(m["category"], "black")
            shaded = get_shaded_color(base_color, idx, total)
            hover = adjust_lightness(shaded, 1.3)

            tag = f"{lineno}_{m['start']}_{m['end']}_{m['name']}"
            if tag not in text_widget.tag_names():
                text_widget.tag_config(tag, background=shaded, underline=m.get('overlap', False))
                text_widget.tag_bind(tag, "<Enter>", lambda e, t=tag, c=hover: text_widget.tag_config(t, background=c))
                text_widget.tag_bind(tag, "<Leave>", lambda e, t=tag, c=shaded: text_widget.tag_config(t, background=c))

            if tag_map is not None:
                tag_map[tag] = m

            start_idx = f"{lineno}.{m['start']}"
            end_idx = f"{lineno}.{m['end']}"
            text_widget.tag_add(tag, start_idx, end_idx)
