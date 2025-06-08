import re
from typing import List, Tuple

def tokenize(s: str) -> List[Tuple[str, str]]:
    tokens = []
    current = ''
    is_sep = None

    for char in s:
        if is_sep is None:
            is_sep = not char.isalnum()

        if (not char.isalnum()) == is_sep:
            current += char
        else:
            tokens.append((current, 'sep' if is_sep else 'token'))
            current = char
            is_sep = not char.isalnum()

    if current:
        tokens.append((current, 'sep' if is_sep else 'token'))

    return tokens
