from unittest import TestCase
from unittest.mock import patch

from validator.parser import XmlParser

class TestXmlParser(TestCase):

    def test_parse_happy_path(self):
        parser = XmlParser(query='.//string')
        actual = parser.parse('tests/fixtures/en/markdown_in_xml.xml')
        self.assertEqual('<p>test text</p>\n<p>test cdata</p>', actual)
