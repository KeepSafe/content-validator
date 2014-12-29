import os
import difflib
from bs4 import BeautifulSoup

from .utils import clean_html_tree


class Diff(object):

    def __init__(self, output_dir):
        self.output_dir = output_dir

    def _pretty_html(self, parser, reader, file_path):
        content = parser.parse(reader.read(file_path))
        soup = BeautifulSoup(content)
        clean_soup = clean_html_tree(soup)
        return soup.prettify()

    def _get_lang(self, path1, path2):
        lang = ''
        for c1, c2 in zip(path1, path2):
            if (c2 == '/' or c2 == '\\') and lang:
                break
            if c1 != c2 or lang:
                lang = lang + c2
        return lang or 'base'

    def diff_to_file(self, parser, reader, base_path, other_path):
        base_name, _ = os.path.splitext(os.path.basename(base_path))
        other_name, _ = os.path.splitext(os.path.basename(other_path))
        output_dir = os.path.join(self.output_dir, base_name)
        base_html = self._pretty_html(parser, reader, base_path)
        other_html = self._pretty_html(parser, reader, other_path)
        lang = self._get_lang(base_path, other_path)

        htmldiff = difflib.HtmlDiff(tabsize=4)
        diff_content = htmldiff.make_file(
            base_html.splitlines(), other_html.splitlines(), context=True)
        diff_path = os.path.join(output_dir, '{}.{}.html'.format(other_name, lang))

        os.makedirs(output_dir, exist_ok=True)
        with open(diff_path, 'w') as fp:
            fp.write(diff_content)

    def error_to_file(self, base_path, other_path, error):
        base_name, _ = os.path.splitext(os.path.basename(base_path))
        other_name, _ = os.path.splitext(os.path.basename(other_path))
        lang = self._get_lang(base_path, other_path)
        output_dir = os.path.join(self.output_dir, lang)
        error_path = os.path.join(output_dir, '{}.txt'.format(other_name, lang))

        os.makedirs(output_dir, exist_ok=True)
        with open(error_path, 'w') as fp:
            fp.write(str(error))

def diff(output_dir):
    return Diff(output_dir)
