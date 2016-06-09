import difflib
from markdown import markdown
import re
from html2text import html2text
from bs4 import BeautifulSoup
from sdiff import diff, renderer

from ..errors import MdDiff, ContentData

LINK_RE = r'\]\(([^\)]+)\)'


def save_file(content, filename):
    with open(filename, 'w') as fp:
        fp.write(content)


class MarkdownComparator(object):

    def check(self, data, parser):
        if not data:
            return []

        # TODO use yield instead of array
        errors = []
        for row in data:
            base = row.pop(0)
            base_content = parser.parse(base)
            for other in row:
                other_content = parser.parse(other)
                other_diff, base_diff, error = diff(other_content, base_content, renderer=renderer.HtmlRenderer())
                broken_links = self.get_broken_links(base_content, other_content)
                if error or broken_links:
                    error_msgs = []
                    if error:
                        error_msgs = map(lambda e: e.message, error)
                    if broken_links:
                        error_msgs = list(error_msgs) + ['There is broken link `%s`' % link for link in broken_links]
                        for link in broken_links:
                            other_diff = other_content.replace(link, '<del>%s</del>' % link)

                    base_data = ContentData(base, base_content, base_diff)
                    other_data = ContentData(other, other_content, other_diff)
                    # TODO horrible
                    errors.append(MdDiff(base_data, other_data, error_msgs))
        return errors
