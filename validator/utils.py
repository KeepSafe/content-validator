import os
from enum import Enum
from lxml import etree
from bs4 import element


# TODO move to a better place
class FileFormat(Enum):
    md = 1
    xml = 2
    txt = 3
    csv = 4

_junk_tag_names = ['strong', 'em']

def _clean_child(node, parent_idx, replace_text):
    if isinstance(node, element.NavigableString):
        node.replace_with(replace_text)
    # elif node.name in _junk_tag_names:
    #     for idx, child in enumerate(node.children):
    #         if not isinstance(child, element.NavigableString):
    #             _clean_child(child, idx)
    #             node.parent.insert(parent_idx, child)
    #             parent_idx = parent_idx + 1
    #     node.decompose()
    else:
        for idx, child in enumerate(node.children):
            _clean_child(child, idx, replace_text)


def clean_html_tree(tree, replace_text=''):
    for idx, node in enumerate(tree.children):
        _clean_child(node, idx, replace_text)
    return tree
