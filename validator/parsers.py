import markdown
import xml.etree.ElementTree as ET

from .fs import read_content


class ParserError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class FileReader(object):
    def read(self, path):
        return read_content(path)


class TxtReader(object):
    def read(self, content):
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
        elements = ET.fromstring(content).findall(self.query)
        text_elements = [element.text.strip() for element in elements]
        return '\n\n'.join(text_elements)


class CsvParser(object):
    def parse(self, content):
        return '\n'.join(content.split(','))


class ChainParser(object):
    def __init__(self, parsers):
        self.parsers = parsers

    def parse(self, content):
        original_content = content
        try:
            for parser in self.parsers:
                content = parser.parse(content)
            return content
        except Exception as e:
            msg = 'error in content %s' % original_content
            raise ParserError(msg) from e
