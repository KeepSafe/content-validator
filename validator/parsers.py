import markdown
import xml.etree.ElementTree as ET

from .fs import read_content


class ParserError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class FileReader:
    def read(self, path):
        return read_content(path)


class TxtReader:
    def read(self, content):
        return content


class MarkdownParser:
    def parse(self, content):
        return markdown.markdown(content)


class XmlParser:
    def __init__(self, query='*'):
        self.query = query

    def parse(self, content):
        content = content.strip()
        if not content:
            return ''
        elements = ET.fromstring(content).findall(self.query)
        text_elements = filter(lambda el: el.text is not None, elements)
        texts = map(lambda el: el.text.strip(), text_elements)
        return '\n\n'.join(texts)


class CsvParser:
    def parse(self, content):
        return '\n'.join(content.split(','))


class ChainParser:
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
