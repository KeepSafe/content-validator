import difflib
import hoep
import re
from html2text import html2text
from bs4 import BeautifulSoup

from ..fs import read_content
from ..model import HtmlDiff


class ReplaceTextContentRenderer(hoep.Hoep):
    _placeholder_pattern = '[placeholder{}]'

    def __init__(self, extensions=0, render_flags=0):
        super(ReplaceTextContentRenderer, self).__init__(extensions, render_flags)
        self._counter = 1
        self._links = 1
        self.mapping = {}

    # def _link(self, link, title, content):
    #     key = self.link_pattern.format(self.links)
    #     self.links += 1
    #     self.mapping[key] = content
    #     return key

    def normal_text(self, text):
        if not text.strip():
            return text
        key = self._placeholder_pattern.format(self._counter)
        self._counter += 1
        self.mapping[key] = text
        return key


class MarkdownComparator(object):
    def _diff(self, base, other, base_mapping, other_mapping):
        diff = difflib.HtmlDiff(tabsize=4).make_table(base.splitlines(), other.splitlines())
        diff_soup = BeautifulSoup(diff, 'html.parser')

        changes = diff_soup.find_all('span', 'diff_chg')
        for change in changes:
            change.replace_with(change.get_text())

        diff_rows = diff_soup.find_all('tr')
        for row in diff_rows:
            cells = row.find_all('td')
            base_cell = str(cells[2])
            other_cell = str(cells[5])
            for k, v in base_mapping.items():
                base_cell = base_cell.replace(k, v, 1)
            for k, v in other_mapping.items():
                other_cell = other_cell.replace(k, v, 1)
            cells[2].replace_with(BeautifulSoup(base_cell))
            cells[5].replace_with(BeautifulSoup(other_cell))
        return str(diff_soup)

    def _parse(self, content):
        renderer = ReplaceTextContentRenderer()
        content_html = renderer.render(content)
        parsed_content = html2text(content_html).strip()
        parsed_content = re.sub(r'\([^\)]*\)', '()', parsed_content)
        return parsed_content, renderer.mapping

    def _compare(self, base, other):
        base_parsed, base_mapping = self._parse(base)
        other_parsed, other_mapping = self._parse(other)

        if base_parsed != other_parsed:
            return self._diff(base_parsed, other_parsed, base_mapping, other_mapping)
        else:
            return ''

    def check(self, paths, parser):
        if not paths:
            return []
            
        diffs = []
        for path_set in paths:
            base_path = path_set.pop(0)
            base = parser.parse(read_content(base_path))
            for other_path in path_set:
                other = parser.parse(read_content(other_path))
                diff = self._compare(base, other)
                if diff:
                    htmldiff = HtmlDiff(base_path, other_path, diff)
                    diffs.append(htmldiff)
        return diffs
        