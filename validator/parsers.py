import markdown
import xml.etree.ElementTree as ET

from .fs import read_content


class ParserError(Exception):
    pass


class FileParser(object):
    def parse(self, path):
        return read_content(path)


class TxtParser(object):
    def parse(self, content):
        return content


class MarkdownParser(object):
    def parse(self, content):
        return markdown.markdown(content)


class XmlParser(object):

    def __init__(self, query='*'):
        self.query = query

    def parse(self, content):
        content = content.strip()
        if not content:
            return ''
        try:
            elements = ET.fromstring(content).findall(self.query)
            text_elements = [element.text.strip() for element in elements]
            return '\n\n'.join(text_elements)
        except Exception as e:
            raise ParserError() from e


class CsvParser(object):
    def parse(self, content):
        return '\n'.join(content.split(','))


class ChainParser(object):

    def __init__(self, parsers):
        self.parsers = parsers

    def parse(self, content):
        for parser in self.parsers:
            content = parser.parse(content)
        return content
