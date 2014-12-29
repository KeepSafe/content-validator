import os
import markdown
import xml.etree.ElementTree as ET

from .utils import FileFormat

class TxtReader(object):

    def read(self, file_path):
        if not os.path.exists(file_path):
            raise ValueError('{} file does not exist'.format(file_path))
        with open(file_path) as fp:
            return fp.read()


class MarkdownParser(object):
    def __init__(self, **kwargs):
        pass

    def parse(self, data):
        return markdown.markdown(data)


class XmlReader(object):
    def __init__(self, **kwargs):
        self.query = kwargs['query']

    def read(self, file_path):
        if not os.path.exists(file_path):
            return ''
        with open(file_path) as fp:
            elements = ET.parse(fp).findall(self.query)
            text_elements = [element.text for element in elements]
            return '\n\n'.join(text_elements)


parsers = {
    FileFormat.md: MarkdownParser,
}

readers = {
    FileFormat.txt: TxtReader,
    FileFormat.xml: XmlReader,
}

def parser(file_format, **kwargs):
    return parsers[file_format](**kwargs)

def reader(file_format, **kwargs):
    return readers[file_format](**kwargs)
