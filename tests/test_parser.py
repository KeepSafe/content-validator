from unittest import TestCase

import pytest

from validator import parsers

from tests.utils import read


class TestPaths(TestCase):
    def test_xml_parsing(self):
        content = read('tests/fixtures/bugs/parser_bug.xml')
        parser = parsers.XmlParser()
        parser.parse(content)


def test_xml_parser_empty_returns_empty():
    parser = parsers.XmlParser()

    assert parser.parse('   ') == ''


def test_chain_parser_wraps_errors():
    parser = parsers.ChainParser([parsers.XmlParser()])

    with pytest.raises(parsers.ParserError) as exc:
        parser.parse('<root><broken></root>')

    assert 'error in content' in str(exc.value)
