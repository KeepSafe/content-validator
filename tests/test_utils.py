from unittest import TestCase
from bs4 import BeautifulSoup
from validator.utils import clean_html_tree


class TestUtils(TestCase):
    def test_clean_html_happy_path(self):
        html = BeautifulSoup('<p>hello<a>world</a></p>')
        actual = clean_html_tree(html)

        self.assertEqual('<html><body><p><a></a></p></body></html>', str(actual))

    def _test_clean_html_remove_junk_tags(self):
        html = BeautifulSoup('<p>hello<strong>world<a>link</a></strong></p>')
        actual = clean_html_tree(html)

        self.assertEqual('<html><body><p><a></a></p></body></html>', str(actual))
