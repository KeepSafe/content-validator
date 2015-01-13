from bs4 import BeautifulSoup

from .fs import save_report

class ContentError(object):
    def __init__(self, path, error):
        self.path = path
        self.error = error


class UrlError(object):

    def __init__(self, urls=None):
        self.urls = {}

    def add_url(self, url, status_code):
        self.urls[url] = status_code

    def has_errors(self):
        return bool(self.urls)

class ComparisonError(object):

    def __init__(self, base_path, other_path, error):
        self.base_path = base_path
        self.other_path = other_path
        self.error = error


class MarkdownError(object):

    def __init__(self, base, other, diff):
        self.base = base
        self.other = other
        self.diff = diff


class HtmlReporter(object):
    report_template = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
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

        <thead>
        <tr><td width="50%" id="left_path"></td><td width="50%" id="right_path"></td></tr>
        </thead>

        <tbody>
        <tr><td width="50%"><p id="left_html"></p></td><td width="50%"><p id="right_html"></p></td></tr>
        </tbody>
    </table>

    <div id="md_diff"></div>

    <div id="urls"></div>
</body>
</html>
"""

    def __init__(self, output_directory='errors'):
        self.output_directory = output_directory

    def _add_content(self, soup, tag_id, content):
        tags = soup.select('#{}'.format(tag_id))
        if tags and content:
            tags[0].append(content)
        return soup


    def report(self, errors):
        for path, error in errors.items():
            report_soup = BeautifulSoup(self.report_template)
            if isinstance(error, ContentError):
                url_error = error.error
                messages = ['<span>{} returned with code {}</span>'.format(url, code) for url, code in url_error.urls.items()]
                self._add_content(report_soup, 'urls', '\n'.join(messages))
            if isinstance(error, ComparisonError):
                md_error = error.error
                report_soup = self._add_content(report_soup, 'left_path', str(error.base_path))
                report_soup = self._add_content(report_soup, 'right_path', str(error.other_path))
                report_soup = self._add_content(report_soup, 'left_html', BeautifulSoup(md_error.base).body)
                report_soup = self._add_content(report_soup, 'right_html', BeautifulSoup(md_error.other).body)
                report_soup = self._add_content(report_soup, 'md_diff', BeautifulSoup(md_error.diff).body)
            save_report(self.output_directory, error.other_path, report_soup.prettify())


class ConsoleReporter(object):
    def report(self, errors):
        for path, error in errors.items():
            if isinstance(error, ContentError):
                url_error = error.error
                print('File {} has errors:'.format(str(path)))
                print(url_error.urls)
                for url, code in url_error.urls.items():
                    print('{} returned with code {}'.format(url, code))
                print()
            if isinstance(error, ComparisonError):
                print('Files are different:\n{}\n{}\n\n'.format(str(error.base_path), str(error.other_path)))
