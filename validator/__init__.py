import sdiff

from . import parsers, checks, reports, fs


class Validator:
    def __init__(self, contents, parser, reader, check, reporter=None):
        self.contents = contents
        self.parser = parser
        self.reader = reader
        self.check = check
        self.reporter = reporter

    def validate(self):
        errors = self.check.check(self.contents, self.parser, self.reader)
        if self.reporter is not None:
            self.reporter.report(errors)
        return errors

    async def async_validate(self):
        errors = await self.check.async_check(self.contents, self.parser, self.reader)
        if self.reporter is not None:
            self.reporter.report(errors)
        return errors


class ReportBuilder:
    def __init__(self, contents, parser, reader, check):
        self.contents = contents
        self.parser = parser
        self.reader = reader
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
        return Validator(self.contents, self.parser, self.reader, self.check, reporter).validate()


class CheckBuilder:
    def __init__(self, contents, content_type, parser, reader):
        self.contents = contents
        self.content_type = content_type
        self.parser = parser
        self.reader = reader
        self.checks = []

    def md(self):
        self.checks.append(checks.markdown(self.content_type,
                                           md_parser_cls=sdiff.MdParser))
        return self

    def zendesk_helpcenter_md(self):
        self.checks.append(checks.markdown(self.content_type,
                                           md_parser_cls=sdiff.ZendeskHelpMdParser))
        return self

    def url(self, **kwargs):
        self.checks.append(checks.urls(self.content_type, **kwargs))
        return self

    def java(self):
        self.checks.append(checks.java_args(self.content_type))
        return self

    def report(self):
        check = checks.ChainCheck(self.checks)
        return ReportBuilder(self.contents, self.parser, self.reader, check)

    def validate(self):
        check = checks.ChainCheck(self.checks)
        return Validator(self.contents, self.parser, self.reader, check).validate()

    async def async_validate(self):
        check = checks.ChainCheck(self.checks)
        res = await Validator(self.contents, self.parser, self.reader, check).async_validate()
        return res


class ParserBuilder:
    def __init__(self, contents, reader=None):
        self.contents = contents
        self.content_type = 'txt'
        self.reader = reader or parsers.TxtReader()
        self.parsers = []

    def html(self):
        self.content_type = 'html'
        return self

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
        return CheckBuilder(self.contents, self.content_type, parser, self.reader)


class ContentBuilder:
    def files(self, pattern, **kwargs):
        contents = fs.files(pattern, **kwargs)
        return ParserBuilder(contents, parsers.FileReader())

    def file(self, base_path, other_path):
        contents = fs.file(base_path, other_path)
        return ParserBuilder(contents, parsers.FileReader())

    def texts(self, contents):
        contents = [contents]
        return ParserBuilder(contents)

    def text(self, base, other):
        contents = [[base, other]]
        return ParserBuilder(contents)


def parse():
    return ContentBuilder()
