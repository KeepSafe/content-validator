import os
import difflib
import html2text
from bs4 import BeautifulSoup

from .utils import clean_html_tree


html_diff = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html>

<head>
    <meta http-equiv="Content-Type"
          content="text/html; charset=ISO-8859-1" />
    <title></title>
    <style type="text/css">
        table.diff {font-family:Courier; border:medium;}
        .diff_header {background-color:#e0e0e0}
        td.diff_header {text-align:right}
        .diff_next {background-color:#c0c0c0}
        .diff_add {background-color:#aaffaa}
        .diff_chg {background-color:#ffff77}
        .diff_sub {background-color:#ffaaaa}
    </style>
</head>

<body>

    <table class="diff" id="difflib_chg_to4__top"
           cellspacing="0" cellpadding="0" rules="groups" >
        <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>
        <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>

        <tbody>
        <tr><td id="left_path"></td><td id="right_path"></td></tr>
        <tr><td><pre id="left_html"></pre></td><td><pre id="right_html"></pre></td></tr>
        </tbody>
    </table>
</body>
</html>
"""


class Diff(object):

    def __init__(self, output_dir):
        self.output_dir = output_dir

    def _pretty_html(self, parser, reader, file_path, replace_txt=''):
        content = parser.parse(reader.read(file_path))
        soup = BeautifulSoup(content)
        clean_soup = clean_html_tree(soup, replace_txt)
        return clean_soup.prettify()

    def _get_lang(self, path1, path2):
        s1 = path1.split('/')
        s2 = path2.split('/')
        for c1, c2 in zip(s1, s2):
            if c1 != c2 or '.' in (c1 + c2):
                return c2
        return 'base'

    def _add_content(self, diff_soup, tag_id, content):
        tags = diff_soup.select('#{}'.format(tag_id))
        if tags:
            tags[0].append(content)

    def html_to_file(self, parser, reader, base_path, other_path):
        base_name, _ = os.path.splitext(os.path.basename(base_path))
        other_name, _ = os.path.splitext(os.path.basename(other_path))
        base_content = parser.parse(reader.read(base_path))
        other_content = parser.parse(reader.read(other_path))
        base_soup = BeautifulSoup(base_content)
        other_soup = BeautifulSoup(other_content)
        lang = self._get_lang(base_path, other_path)
        output_dir = os.path.join(self.output_dir, lang)

        diff_soup = BeautifulSoup(html_diff)
        self._add_content(diff_soup, 'left_path', base_path)
        self._add_content(diff_soup, 'right_path', other_path)
        self._add_content(diff_soup, 'left_html', base_soup.prettify())
        self._add_content(diff_soup, 'right_html', other_soup.prettify())

        diff_content = diff_soup.prettify()
        diff_path = os.path.join(output_dir, '{}.html'.format(other_name))

        os.makedirs(output_dir, exist_ok=True)
        with open(diff_path, 'w') as fp:
            fp.write(diff_content)

    def error_to_file(self, base_path, other_path, error):
        base_name, _ = os.path.splitext(os.path.basename(base_path))
        other_name, _ = os.path.splitext(os.path.basename(other_path))
        lang = self._get_lang(base_path, other_path)
        output_dir = os.path.join(self.output_dir, lang)
        error_path = os.path.join(output_dir, '{}.txt'.format(other_name))

        os.makedirs(output_dir, exist_ok=True)
        with open(error_path, 'w') as fp:
            fp.write(str(error))


    def diff_to_file(self, parser, reader, base_path, other_path):
        base_html = self._pretty_html(parser, reader, base_path, 'placeholder')
        other_html = self._pretty_html(parser, reader, other_path, 'placeholder')
        base_name, _ = os.path.splitext(os.path.basename(base_path))
        other_name, _ = os.path.splitext(os.path.basename(other_path))
        lang = self._get_lang(base_path, other_path)
        output_dir = os.path.join(self.output_dir, lang)

        base_text = html2text.html2text(base_html)
        other_text = html2text.html2text(other_html)
        htmldiff = difflib.HtmlDiff(tabsize=4)
        diff_content = htmldiff.make_file(base_text.splitlines(), other_text.splitlines(), context=True)
        diff_path = os.path.join(output_dir, '{}.md.html'.format(other_name))

        os.makedirs(output_dir, exist_ok=True)
        with open(diff_path, 'w') as fp:
            fp.write(diff_content)

def diff(output_dir):
    return Diff(output_dir)
