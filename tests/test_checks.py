from unittest import TestCase
from unittest.mock import patch

from validator.checks import TxtUrlCheck, HtmlUrlCheck, MarkdownComparator


class TestTxtUrlChecker(TestCase):

    def setUp(self):
        self.check = TxtUrlCheck()

    @patch('requests.get')
    def test_happy_path(self, mock_get):
        content = 'aaa http://www.google.com aaa'
        mock_get.return_value.status_code = 200

        errors = self.check._check_content(content)

        self.assertIsNone(errors)

    @patch('requests.get')
    def test_not_found(self, mock_get):
        content = 'aaa http://www.google.com aaa'
        mock_get.return_value.status_code = 404

        errors = self.check._check_content(content)

        self.assertIsNotNone(errors)

    @patch('requests.get')
    def test_retry_for_server_error(self, mock_get):
        content = 'aaa http://www.google.com aaa'
        mock_get.return_value.status_code = 500

        errors = self.check._check_content(content)

        self.assertEqual(3, mock_get.call_count)

    @patch('requests.get')
    def test_make_only_one_request_per_unique_url(self, mock_get):
        content = 'aaa http://www.google.com aaa http://www.google.com aaa'
        mock_get.return_value.status_code = 200

        errors = self.check._check_content(content)

        self.assertEqual(1, mock_get.call_count)

    @patch('requests.get')
    def test_skip_request_parameterized_urls(self, mock_get):
        content = 'aaa http://{{url}} aaa'
        mock_get.return_value.status_code = 200

        errors = self.check._check_content(content)

        self.assertFalse(mock_get.called)

    @patch('requests.get')
    def test_skip_empty_urls(self, mock_get):
        content = 'aaa http:// aaa'
        mock_get.return_value.status_code = 200

        errors = self.check._check_content(content)

        self.assertFalse(mock_get.called)


class TestHtmlUrlChecker(TestCase):

    def setUp(self):
        self.check = HtmlUrlCheck()

    @patch('requests.get')
    def test_happy_path(self, mock_get):
        content = '<a href="http://www.google.com">link</a>'
        mock_get.return_value.status_code = 200

        errors = self.check._check_content(content)

        self.assertIsNone(errors)

    @patch('requests.get')
    def test_url_in_text_no_href(self, mock_get):
        content = '<a>http://www.google.com</a>'
        mock_get.return_value.status_code = 200

        errors = self.check._check_content(content)

        self.assertIsNone(errors)

    @patch('requests.get')
    def test_image(self, mock_get):
        content = '<img src="http://www.google.com">'
        mock_get.return_value.status_code = 200

        self.check._check_content(content)

        self.assertTrue(mock_get.called)

    @patch('requests.get')
    def test_skip_request_parameterized_urls(self, mock_get):
        content = '<a href="http://{{url}}">link</a>'
        mock_get.return_value.status_code = 200

        self.check._check_content(content)

        self.assertFalse(mock_get.called)

    @patch('requests.get')
    def test_skip_empty_urls(self, mock_get):
        content = '<a href="http://">link</a>'
        mock_get.return_value.status_code = 200

        self.check._check_content(content)

        self.assertFalse(mock_get.called)


def read(path):
    with open(path) as fp:
        return fp.read()


#TODO those IsNotNone tests are stupid, we should return something that is testable and convert it to error messages
class TestMarkdownComparator(TestCase):
    def _test_markdown(self, path1, path2):
        comparator = MarkdownComparator()
        md1= read(path1)
        md2 = read(path2)
        return comparator._compare(md1, md2)

    def test_markdown_same(self):
        error = self._test_markdown('tests/fixtures/lang/en/test1.md', 'tests/fixtures/lang/de/test1.md')
        self.assertIsNone(error)

    def test_markdown_different(self):
        error = self._test_markdown('tests/fixtures/lang/en/test2.md', 'tests/fixtures/lang/de/test2.md')
        self.assertIsNotNone(error)

    def test_diff(self):
        comparator = MarkdownComparator()
        comparator._compare('# Congratulations!!!', '# ¡Felicitaciones!')
