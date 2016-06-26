from bs4 import BeautifulSoup
import shutil
import markdown

from .fs import save_report
from .errors import UrlDiff, MdDiff


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
        ins {background-color: lightgreen;}
        del {background-color: red;}
        .info_text {margin-bottom: 15px;}
    </style>
</head>

<body>

    <div class="info-text">
        <h3>KeepSafe's validation tool has found some problems with the translation</h3>
        <p>
            The elements on the left show the reference text, the elements on the right the translation.<br />
            The elements that are missing are highlighted in green,
            the ones which are unnecessary are highlighted in red. <br />
            The tool is not always 100% accurate, sometimes it might show things
            that are correct as errors if there are other errors in the text. <br />
            Please correct the errors you can find first.
            If you think the text is correct and the tool is still showing errors please contact KeepSafe's employee.
        </p>
    </div>

    <h4>This is how the text will look to the user</h4>
    <table class="diff" id="difflib_chg_to4__top"
           cellspacing="0" cellpadding="0" rules="groups" >
        <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>
        <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>

        <tbody>
        <tr><td width="50%"><p id="left_content"></p></td><td width="50%"><p id="right_content"></p></td></tr>
        </tbody>
    </table>

    <h4>This is the original text</h4>
    <table class="diff" id="difflib_chg_to4__top"
           cellspacing="0" cellpadding="0" rules="groups" >
        <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>
        <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>

        <tbody>
        <tr><td width="50%"><p id="left_diff"></p></td><td width="50%"><p id="right_diff"></p></td></tr>
        </tbody>
    </table>

    <div>
        <h4>Errors found:</h4>
        <p id="error_msgs"></p>
    </div>

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
        else:
            print('missing tag: %s, content %s' % (tag_id, content))
        return soup

    # TODO just rewrite !!!
    # TODO remove isinstance
    def report(self, errors):
        shutil.rmtree(self.output_directory, ignore_errors=True)
        for error in errors:
            # TODO save to different files for links and diff
            # TODO use mustache for templates
            report_soup = BeautifulSoup(self.report_template)
            if isinstance(error, UrlDiff):
                messages = ['<span>{} returned with code {}</span>'.format(error.url, error.status_code)]
                self._add_content(report_soup, 'urls', '\n'.join(messages))
            if isinstance(error, MdDiff):
                error_msgs = '<br />'.join(map(lambda i: str(i), error.error_msgs))
                base = markdown.markdown(error.base.parsed)
                other = markdown.markdown(error.other.parsed)
                report_soup = self._add_content(report_soup, 'left_content', BeautifulSoup(base).body)
                report_soup = self._add_content(report_soup, 'right_content', BeautifulSoup(other).body)
                report_soup = self._add_content(report_soup, 'left_diff', BeautifulSoup(error.base.diff).body)
                report_soup = self._add_content(report_soup, 'right_diff', BeautifulSoup(error.other.diff).body)
                report_soup = self._add_content(report_soup, 'error_msgs', BeautifulSoup(error_msgs).body)
            target_path = error.other.original
            target_path = target_path.__class__(str(target_path).replace('../',''))
            save_report(self.output_directory, target_path, report_soup.prettify())


class ConsoleReporter(object):

    def report(self, errors):
        for error in errors:
            if isinstance(error, UrlDiff):
                print('{} returned with code {}'.format(error.url, error.status_code))
                for path in error.files:
                    print('\t{}'.format(str(path)))
                print()
            if isinstance(error, MdDiff):
                print('Files are different:\n\t{}\n\t{}\n\n'.format(str(error.base_path), str(error.other_path)))


class StoreReporter(object):

    def __init__(self):
        self.log = []

    def report(self, errors):
        for error in errors:
            if isinstance(error, UrlDiff):
                self.log.append('%s returned with code %s for files' % (error.url, error.status_code))
                for path in error.files:
                    self.log.append('\t%s' % str(path))
            if isinstance(error, MdDiff):
                self.log.append('Files are different:\n\t%s\n\t%s\n\n' % (str(error.base_path), str(error.other_path)))


class ChainReporter(object):
    def __init__(self, reporters):
        self.reporters = reporters

    def report(self, errors):
        for reporter in self.reporters:
            reporter.report(errors)
