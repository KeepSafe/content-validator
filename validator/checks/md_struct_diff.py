import difflib
from markdown import markdown
import re
from html2text import html2text
from bs4 import BeautifulSoup
from sdiff import diff, renderer

from ..fs import read_content
from ..model import HtmlDiff


def save_file(content, filename):
    with open(filename, 'w') as fp:
        fp.write(content)


class MarkdownComparator(object):

    def check(self, paths, parser):
        if not paths:
            return []

        errors = []
        for path_set in paths:
            base_path = path_set.pop(0)
            base = parser.parse(read_content(base_path))
            for other_path in path_set:
                other = parser.parse(read_content(other_path))
                other_diff, base_diff, error = diff(other, base, renderer=renderer.HtmlRenderer())
                if error:
                    htmldiff = HtmlDiff(base_path, markdown(base), base_diff, other_path, markdown(other), other_diff, error)
                    errors.append(htmldiff)
        return errors
