import re
from typing import List, Optional

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class EnumRegexGenerator:
    def __init__(self, words: List[str], ignore_case: bool = False,
                 sort_by_length: bool = False, group_name: Optional[str] = None,
                 optional: bool = False):
        self.root = TrieNode()
        self.ignore_case = ignore_case
        self.sort_by_length = sort_by_length
        self.group_name = group_name
        self.optional = optional

        for word in set(words):  # Удаление дубликатов
            self._insert(word)

    def _insert(self, word: str):
        node = self.root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        node.is_end = True

    def _collect_words(self, node: TrieNode = None, prefix: str = "", results=None):
        if results is None:
            results = []
        if node is None:
            node = self.root
        if node.is_end:
            results.append(prefix)
        for char, child in node.children.items():
            self._collect_words(child, prefix + char, results)
        return results

    def generate(self) -> str:
        words = self._collect_words()
        if self.sort_by_length:
            words.sort(key=lambda x: -len(x))
        else:
            words.sort()

        base = '(?:' + '|'.join(map(re.escape, words)) + ')'

        if self.ignore_case:
            base = f'(?i:{base})'
        if self.group_name:
            base = f'(?P<{self.group_name}>{base})'
        if self.optional:
            base = f'(?:{base})?'

        return base
