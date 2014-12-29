from unittest import TestCase
from unittest.mock import patch

from validator.parser import XmlReader

class TestXmlParser(TestCase):

    def test_parse_happy_path(self):
        parser = XmlReader(query='.//string')
        actual = parser.read('tests/fixtures/en/markdown_in_xml.xml')
        self.assertEqual('test text\n\ntest cdata', actual)
