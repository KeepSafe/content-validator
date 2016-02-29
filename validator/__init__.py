import logging
import sys
from enum import Enum
from collections import defaultdict
from pathlib import Path
from markdown import markdown

from . import cmd, parsers, checks, reports, fs


logger = logging.getLogger()

class Validator(object):
    def __init__(self, contents, parser, check, reporter=None):
        self.contents = contents
        self.parser = parser
        self.check = check
        self.reporter = reporter

    def validate(self):
        errors = self.check.check(self.contents, self.parser)
        if self.reporter is not None:
            self.reporter.report(errors)
        return errors


class ReportBuilder(object):
    def __init__(self, contents, parser, check):
        self.contents = contents
        self.parser = parser
        self.check = check
        self.reporters = []

    def html(self, output_directory='errors'):
        self.reporters.append(reports.HtmlReporter(output_directory))
        return self

    def console(self):
        self.reporters.append(reports.ConsoleReporter())
        return self

    def store(self):
        self.reporters.append(reports.StoreReporter())
        return self

    def validate(self):
        reporter = reports.ChainReporter(self.reporters)
        return Validator(self.contents, self.parser, self.check, reporter).validate()


class CheckBuilder(object):
    def __init__(self, contents, content_type, parser):
        self.contents = contents
        self.content_type = content_type
        self.parser = parser
        self.checks = []

    def md(self):
        self.checks.append(checks.markdown(self.content_type))
        return self

    def url(self, **kwargs):
        self.checks.append(checks.urls(self.content_type, **kwargs))
        return self

    def java(self):
        self.checks.append(checks.java_args(self.content_type))
        return self

    def report(self):
        check = checks.ChainCheck(self.checks)
        return ReportBuilder(self.contents, self.parser, check)

    def validate(self):
        check = checks.ChainCheck(self.checks)
        return Validator(self.contents, self.parser, check).validate()


class ParserBuilder(object):
    def __init__(self, contents, first_parser):
        self.contents = contents
        # TODO use enum
        self.content_type = 'txt'
        self.parsers = [first_parser]

    def md(self):
        self.content_type = 'html'
        self.parsers.append(parsers.MarkdownParser())
        return self

    def xml(self, query='*'):
        self.content_type = 'txt'
        self.parsers.append(parsers.XmlParser(query))
        return self

    def csv(self):
        self.content_type = 'txt'
        self.parsers.append(parsers.CsvParser())
        return self

    def check(self):
        parser = parsers.ChainParser(self.parsers)
        return CheckBuilder(self.contents, self.content_type, parser)


class ContentBuilder(object):
    def files(self, pattern, **kwargs):
        contents = fs.files(pattern, **kwargs)
        return ParserBuilder(contents, parsers.FileParser())

    def file(self, base_path, other_path):
        contents = [[Path(base_path), Path(other_path)]]
        return ParserBuilder(contents, parsers.FileParser())

    def texts(self, contents):
        contents = [contents]
        return ParserBuilder(contents, parsers.TxtParser())

    def text(self, base, other):
        contents = [[base, other]]
        return ParserBuilder(contents, parsers.TxtParser())


def parse():
    return ContentBuilder()

def validate_formatting(settings):
    errors = parse().files(settings.source, lang=settings.base_locale).xml(
    query='.//string').check().md().validate()
    
    if errors:
        logger.info('Errors: %d' % len(errors))
        report_uri = reports.HtmlSummaryReporter(settings.output).report(errors).uri_path
        logger.info('See %s' % report_uri)
        return False
    else:
        return True

def init_log(verbose):
    log_level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    logger.setLevel(log_level)
    logger.addHandler(handler)


def main():
    args = cmd.read_args()
    if args.version:
        result = cmd.print_version()
    else:
        settings = cmd.read_settings(args)
        init_log(settings.verbose)
        valid = validate_formatting(settings)
        sys.exit(0) if not valid else sys.exit(1)
