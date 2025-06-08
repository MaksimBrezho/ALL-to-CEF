import re
from typing import List, Literal, Optional
from .enum_generator import EnumRegexGenerator
from .generalizer import generalize_token
from core.tokenizer.tokenizer import tokenize
from utils.text_utils import common_prefix, common_suffix


def _lcs(a: List[str], b: List[str]) -> List[str]:
    """Return the longest common subsequence of two lists."""
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a)):
        for j in range(len(b)):
            if a[i] == b[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i + 1][j], dp[i][j + 1])

    i, j = len(a), len(b)
    result = []
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            result.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return list(reversed(result))


def _merge_tokens_regex(lines_tokens: List[List[str]], *, case_insensitive: bool) -> str:
    """Merge text tokens across lines using common anchors."""
    if not lines_tokens:
        return ''

    anchors = lines_tokens[0]
    for tokens in lines_tokens[1:]:
        anchors = _lcs(anchors, tokens)
        if not anchors:
            break

    segments_per_line = []
    for tokens in lines_tokens:
        segs = []
        idx = 0
        for anchor in anchors:
            try:
                j = tokens.index(anchor, idx)
            except ValueError:
                j = len(tokens)
            segs.append(' '.join(tokens[idx:j]))
            idx = j + 1
        segs.append(' '.join(tokens[idx:]))
        segments_per_line.append(segs)

    def build_seg_regex(values: List[str], with_space: bool) -> str:
        unique_vals = list(dict.fromkeys(values))
        if len(unique_vals) == 1 and unique_vals[0] == '':
            return ''
        if len(unique_vals) == 2 and '' in unique_vals:
            other = unique_vals[0] if unique_vals[1] == '' else unique_vals[1]
            base = re.escape(other)
            prefix = "\\s+" if with_space else ""
            return rf'(?:{prefix}{base})?'
        if len(unique_vals) == 1:
            base = re.escape(unique_vals[0])
            prefix = "\\s+" if with_space else ""
            return rf'{prefix}{base}'
        alt_vals = [v for v in unique_vals if v != '']
        alt = EnumRegexGenerator(alt_vals, ignore_case=case_insensitive, sort_by_length=True).generate()
        if '' in unique_vals:
            prefix = "\\s+" if with_space else ""
            return rf'(?:{prefix}{alt})?'
        prefix = "\\s+" if with_space else ""
        return rf'{prefix}{alt}'

    parts: List[str] = []
    seg_count = len(anchors) + 1

    # first segment (no leading whitespace)
    seg_regex = build_seg_regex([segments[0] for segments in segments_per_line], with_space=False)
    if seg_regex:
        parts.append(seg_regex)

    if anchors:
        parts.append(re.escape(anchors[0]))

    for idx in range(1, seg_count):
        seg_regex = build_seg_regex([segments[idx] for segments in segments_per_line], with_space=True)
        if seg_regex:
            parts.append(seg_regex)
        if idx < len(anchors):
            parts.append(r'\s+' + re.escape(anchors[idx]))

    return ''.join(parts)

KEY_VALUE_SEPARATORS = {'=', ':', '->', '=>', '<-'}

DigitMode = Literal["standard", "always_fixed_length", "always_plus", "min_length", "fixed_and_min"]

def build_draft_regex_from_examples(
        lines: List[str], *,
        digit_mode: DigitMode = "standard",
        digit_min_length: int = 1,
        case_insensitive: bool = False,
        window_left: Optional[str] = None,
        window_right: Optional[str] = None,
        merge_text_tokens: bool = True,
        max_enum_options: int = 10,
        prefer_alternatives: bool = True,
        merge_by_common_prefix: bool = True,
) -> str:
    token_columns = []
    sep_columns = []
    tokens_by_line: List[List[str]] = []

    leading_prefix = ""
    parsed_pairs = []
    for line in lines:
        pairs = tokenize(line.strip())
        parsed_pairs.append(pairs)
    if parsed_pairs and all(p and p[0][1] == 'sep' for p in parsed_pairs):
        first_vals = {p[0][0] for p in parsed_pairs}
        if len(first_vals) == 1:
            leading_prefix = re.escape(parsed_pairs[0][0][0])
            for p in parsed_pairs:
                p.pop(0)

    for pairs in parsed_pairs:
        
        tokens = [val for val, kind in pairs if kind == 'token']
        seps = [val for val, kind in pairs if kind == 'sep']

        tokens_by_line.append(tokens)

        if not token_columns:
            token_columns = [[] for _ in tokens]
            sep_columns = [[] for _ in seps]

        for i, token in enumerate(tokens):
            token_columns[i].append(token)
        for i, sep in enumerate(seps):
            sep_columns[i].append(sep)

    token_counts = [len(toks) for toks in tokens_by_line]
    if merge_text_tokens and len(set(token_counts)) > 1:
        core = _merge_tokens_regex(tokens_by_line, case_insensitive=case_insensitive)
        if window_left:
            core = f"(?<={re.escape(window_left)})" + core
        if window_right:
            core = core + f"(?={re.escape(window_right)})"
        return core

    def digit_pattern(values: List[str]) -> str:
        lengths = [len(v) for v in values]
        min_len, max_len = min(lengths), max(lengths)
        unique_vals = set(values)

        if digit_mode == "always_plus":
            return r"\d+"
        elif digit_mode == "always_fixed_length":
            return rf"\d{{{len(values[0])}}}"
        elif digit_mode == "fixed_and_min":
            if len(unique_vals) == 1:
                return rf"\d{{{len(values[0])}}}"  # точно фиксированное
            else:
                return rf"\d{{{digit_min_length},{max_len}}}"  # fallback
        elif digit_mode == "min_length":
            return rf"\d{{{digit_min_length},{max_len}}}" if digit_min_length != max_len else rf"\d{{{digit_min_length}}}"
        else:  # "standard"
            if len(unique_vals) == 1:
                return re.escape(values[0])
            elif min_len == max_len:
                return rf"\d{{{min_len}}}"
            elif max_len <= 5:
                return rf"\d{{{min_len},{max_len}}}"
            else:
                return r"\d+"

    token_patterns = []
    i = 0
    token_len = len(token_columns)
    sep_len = len(sep_columns)
    sep_i = 0

    while i < token_len:
        if i + 1 < token_len and sep_i < sep_len:
            sep = sep_columns[sep_i][0]
            if sep == ':' and not all(': ' in line or ':,' in line for line in lines):
                sep = None

            if sep in KEY_VALUE_SEPARATORS:
                keys = token_columns[i]
                values = token_columns[i + 1]

                key_pattern = re.escape(keys[0]) if len(set(keys)) == 1 else generalize_token(keys[0])

                if all(re.fullmatch(r'\d+', tok) for tok in values):
                    value_pattern = digit_pattern(values)
                elif len(set(values)) == 1:
                    value_pattern = re.escape(values[0])
                elif all(re.fullmatch(r'[A-Z]+', t) for t in values):
                    value_pattern = EnumRegexGenerator(values, ignore_case=case_insensitive, sort_by_length=True).generate()
                else:
                    value_pattern = generalize_token(values[0])

                token_patterns.append(f"{key_pattern}{re.escape(sep)}{value_pattern}")
                i += 2
                sep_i += 1
                if sep_i < sep_len:
                    token_patterns.append(re.escape(sep_columns[sep_i][0]))
                    sep_i += 1
                continue

        col = token_columns[i]
        unique_values = list(dict.fromkeys(col))

        if all(re.fullmatch(r'\d+', tok) for tok in col):
            pattern = digit_pattern(col)
        elif len(unique_values) == 1:
            pattern = re.escape(unique_values[0])
        elif prefer_alternatives and all(re.fullmatch(r'[A-Za-z]+', t) for t in unique_values) and len(unique_values) <= max_enum_options:
            if merge_by_common_prefix and len(unique_values) > 1:
                prefix = common_prefix(unique_values)
                suffix = common_suffix(unique_values)
                stripped = [t[len(prefix):len(t)-len(suffix) if suffix else len(t)] for t in unique_values]
                alt = EnumRegexGenerator(stripped, ignore_case=case_insensitive, sort_by_length=True).generate()
                pattern = f"{re.escape(prefix)}{alt}{re.escape(suffix)}"
            else:
                pattern = EnumRegexGenerator(unique_values, ignore_case=case_insensitive, sort_by_length=True).generate()
        elif all(re.fullmatch(r'[A-Z]+', t) for t in col):
            pattern = EnumRegexGenerator(col, ignore_case=case_insensitive, sort_by_length=True).generate()
        else:
            pattern = generalize_token(col[0])

        token_patterns.append(pattern)

        if sep_i < sep_len:
            token_patterns.append(re.escape(sep_columns[sep_i][0]))
            sep_i += 1

        i += 1

    core_pattern = ''.join(token_patterns)
    if leading_prefix:
        core_pattern = leading_prefix + core_pattern

    if window_left:
        core_pattern = f"(?<={re.escape(window_left)}){core_pattern}"
    if window_right:
        core_pattern = f"{core_pattern}(?={re.escape(window_right)})"

    core_pattern = core_pattern.strip()
    return core_pattern
