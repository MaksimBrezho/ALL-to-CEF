"""Simple transformation helpers for CEF field values."""

from __future__ import annotations

import re
from datetime import timezone
from dateutil import parser as date_parser
from typing import Any, Dict, List


def _normalize_time(value: str) -> str:
    """Parse an arbitrary date string and return ISO-8601 in UTC."""
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
    """Apply a basic string transformation."""
    if value is None:
        value = ""
    if transform == "lower":
        return value.lower()
    if transform == "upper":
        return value.upper()
    if transform == "capitalize":
        # Capitalize each word rather than just the first character
        return value.title()
    if transform == "sentence":
        return value[:1].upper() + value[1:].lower() if value else value
    if transform == "time":
        return _normalize_time(value)
    return value


def _reorder_tokens(value: str, regex: str, order: List[int]) -> str:
    """Reorder regex-derived tokens according to the provided order."""
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
        tokens = [t for t in re.split(r"([a-zA-Z]+|\d+|\W)", span) if t]
    return "".join(tokens[i] for i in order if i < len(tokens))


def apply_transform(value: str, transform: Any) -> str:
    """Apply a basic or advanced transformation."""
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



