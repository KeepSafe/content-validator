from unittest import TestCase

from validator import parsers

from tests.utils import read


class TestPaths(TestCase):
    def test_xml_parsing(self):
        content = read('tests/fixtures/bugs/parser_bug.xml')
        parser = parsers.XmlParser()
        parser.parse(content)
