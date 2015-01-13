import hoep
import xml.etree.ElementTree as ET

from .fs import Filetype



class TxtParser(object):

    def __init__(self, **kwargs):
        pass

    def parse(self, content):
        return content.strip()


class MarkdownParser(object):

    def __init__(self, **kwargs):
        pass

    def parse(self, content):
        return hoep.render(content)


class XmlParser(object):

    def __init__(self, **kwargs):
        self.query = kwargs.get('query', '*')

    def parse(self, content):
        if not content:
            return ''
        elements = ET.fromstring(content).findall(self.query)
        text_elements = [element.text for element in elements]
        return '\n\n'.join(text_elements)


class CsvParser(object):

    def __init__(self, **kwargs):
        pass

    def parse(self, content):
        return '\n'.join(content.split(','))



class ChainParser(object):

    def __init__(self, **kwargs):
        self.parsers = kwargs.get('parsers', [])

    def parse(self, content):
        for parser in self.parsers:
            content = parser.parse(content)
        return content


parsers = {
    Filetype.txt: TxtParser,
    Filetype.md: MarkdownParser,
    Filetype.xml: XmlParser,
    Filetype.csv: CsvParser
}


def create_parser(filetype, **kwargs):
    return parsers[filetype](**kwargs)


def chain_parsers(parser_types, **kwargs):
    parsers = [create_parser(parser_type, **kwargs) for parser_type in parser_types]
    return ChainParser(parsers=parsers)
