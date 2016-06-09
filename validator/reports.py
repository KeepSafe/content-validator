from bs4 import BeautifulSoup
import logging
import sys
import shutil
import markdown
import pystache

from .fs import save_report, read_content, save_summary_report
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
            The elements that are missing are highlighted in green, the ones which are unnecessary are highlighted in red. <br />
            The tool is not always 100% accurate, sometimes it might show things that are correct as errors if there are other errors in the text. <br />
            Please correct the errors you can find first. If you think the text is correct and the tool is still showing errors please contact KeepSafe's employee.
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
            save_report(self.output_directory, error.other.original, report_soup.prettify())


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

class HtmlSummaryReporter(object):
    report_template = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->
    <title>KS Content-validator</title>

    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">

    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
      <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->
    <style>
        ins { background: #dff0d8; }
        del { background: #f2dede; }
        body { padding-top: 70px; }
    </style>
</head>
<body data-spy="scroll" data-target="#filelist">
    <nav class="navbar navbar-default navbar-fixed-top" id="filelist">
        <div class="container-fluid">
            <div class="navbar-header">
                <ul class="nav navbar-nav">
                    <li class="dropdown">
                        <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Files<span class="caret"></span></a>
                        <ul class="dropdown-menu">
                            {{#files}}
                                <li><a href="#{{id}}">{{name}}</a></li>
                            {{/files}}
                        </ul>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="row">
        <div class="col-sm-12">
            <div class="alert alert-warning" role="alert">
                <h3>KeepSafe's validation tool has found some problems with the translation</h3>
                <p>
                    The elements on the left show the reference text, the elements on the right the translation.<br />
                    The elements that are missing are highlighted in green, the ones which are unnecessary are highlighted in red. <br />
                    The tool is not always 100% accurate, sometimes it might show things that are correct as errors if there are other errors in the text. <br />
                    Please correct the errors you can find first. If you think the text is correct and the tool is still showing errors please contact KeepSafe's employee.
                </p>
            </div>

            {{#files}}
                <div class="panel panel-default" id="{{id}}">
                    <div class="panel-heading">
                        <h3 class="panel-title">{{name}}</h3>
                    </div>
                    <div class="panel-body">
                        <h5>This is how the text will look to the user</h5>
                        <div class="row">
                            <div class="col-sm-6"><pre>{{{details.lc}}}</pre></div> 
                            <div class="col-sm-6"><pre>{{{details.rc}}}</pre></div> 
                        </div>
                         
                        <h5>This is the original text</h5>
                        <div class="row">
                            <div class="col-sm-6"><pre>{{{details.ld}}}</pre></div> 
                            <div class="col-sm-6"><pre>{{{details.rd}}}</pre></div> 
                        </div>
                        <div class="alert alert-danger" role="alert">
                            <ol>
                                {{#details.errors}}
                                    <li>{{.}}</li>
                                {{/details.errors}}
                            </ol>
                        </div>
                    </div>
                </div>
            {{/files}}
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js" integrity="sha384-0mSbJDEHialfmuBBQP6A4Qrprq5OVfW37PRR3j5ELqxss1yVqOtnepnHVP9aJ7xS" crossorigin="anonymous"></script>
</body>
</html>
"""

    def __init__(self, output_filepath='errors/summary.html'):
        self.output_filepath = output_filepath
        self.uri_path = None

    def report(self, errors):
        files = {}
        for error in errors:
            filename = str(error.other.original)
            files[filename] = files.get(filename, {'errors':[] })
            if isinstance(error, UrlDiff):
                files[filename]['errors'].append("%s returned with code %s" % (error.url, error.status_code))
            if isinstance(error, MdDiff):
                files[filename]['errors'] += list(error.error_msgs)
                files[filename]['lc'] = markdown.markdown(error.base.parsed)
                files[filename]['rc'] = markdown.markdown(error.other.parsed)
                files[filename]['ld'] = error.base.diff
                files[filename]['rd'] = error.other.diff
        data = [{'name': k, 'details': v} for k,v in files.items()]
        for i in range(0,len(data)):
            data[i]['id'] = 'file_%s' % i
        content = pystache.render(self.report_template, {'files': data})
        self.uri_path = save_summary_report(self.output_filepath, content)
        return self
