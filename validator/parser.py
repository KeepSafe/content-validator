import os
import markdown
import xml.etree.ElementTree as ET

from .utils import FileFormat


class MarkdownParser(object):
    def __init__(self, **kwargs):
        pass

    def parse(self, file_path):
        if not os.path.exists(file_path):
            raise ValueError('{} file does not exist'.format(file_path))
        with open(file_path) as fp:
            data = fp.read()
            return markdown.markdown(data)


class XmlParser(object):
    def __init__(self, **kwargs):
        self.query = kwargs['query']

    def parse(self, file_path):
        if not os.path.exists(file_path):
            return ''
        with open(file_path) as fp:
            elements = ET.parse(fp).findall(self.query)
            md_elements = [element.text for element in elements]
            html_elements = [markdown.markdown(element) for element in md_elements]
            return '\n'.join(html_elements)


parsers = {
    FileFormat.md: MarkdownParser,
    FileFormat.xml: XmlParser
}


def parser(file_format, **kwargs):
    return parsers[file_format](**kwargs)
