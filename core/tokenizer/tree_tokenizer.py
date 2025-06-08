from typing import List, Tuple

class StructuredTokenNode:
    def __init__(self, value: str, kind: str = 'token', children=None):
        self.value = value
        self.kind = kind  # 'token', 'sep', 'group', 'root'
        self.children: List[StructuredTokenNode] = children if children else []

    def __repr__(self):
        return f"{self.kind.upper()}({self.value!r}, children={len(self.children)})"


def build_token_tree(s: str) -> StructuredTokenNode:
    root = StructuredTokenNode("ROOT", kind="root")
    stack = [root]
    current = ''
    is_sep = None

    group_open = {'(': ')', '{': '}', '[': ']', '"': '"', "'": "'"}
    group_end_stack = []
    group_buffer_stack = []

    i = 0
    while i < len(s):
        char = s[i]

        if group_end_stack:
            if char == group_end_stack[-1]:
                if current:
                    group_buffer_stack[-1] += current
                    current = ''
                group_content = group_buffer_stack.pop()
                subtree = build_token_tree(group_content)
                stack[-1].children.extend(subtree.children)
                group_end_stack.pop()
                stack.pop()
            else:
                group_buffer_stack[-1] += char
            i += 1
            continue

        if char in group_open:
            if current:
                stack[-1].children.append(StructuredTokenNode(current, kind='sep' if is_sep else 'token'))
                current = ''
            group_end_stack.append(group_open[char])
            group_buffer_stack.append('')
            group_node = StructuredTokenNode(char + "...", kind='group')
            stack[-1].children.append(group_node)
            stack.append(group_node)
            is_sep = None
        else:
            if is_sep is None:
                is_sep = not char.isalnum()

            if (not char.isalnum()) == is_sep:
                current += char
            else:
                if current:
                    stack[-1].children.append(StructuredTokenNode(current, kind='sep' if is_sep else 'token'))
                current = char
                is_sep = not char.isalnum()

        i += 1

    if current:
        stack[-1].children.append(StructuredTokenNode(current, kind='sep' if is_sep else 'token'))

    return root


def flatten_token_tree(node: StructuredTokenNode) -> List[Tuple[str, str]]:
    result = []
    if node.kind in ('token', 'sep'):
        result.append((node.value, node.kind))
    for child in node.children:
        result.extend(flatten_token_tree(child))
    return result
