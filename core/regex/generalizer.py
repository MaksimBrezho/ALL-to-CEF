import re

def generalize_token(token: str) -> str:
    if re.fullmatch(r'\d+', token):
        length = len(token)
        return rf'\d{{{length}}}' if length <= 4 else r'\d+'

    if re.fullmatch(r'[a-zA-Z]+', token):
        return r'[a-zA-Z]+'

    if re.fullmatch(r'\w+', token):
        return r'\w+'

    if re.fullmatch(r'[\w\-]+', token):
        return r'[\w\-]+'

    return re.escape(token)

