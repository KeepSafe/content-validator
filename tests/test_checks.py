from unittest import TestCase
from unittest.mock import patch, MagicMock

from validator.checks import TxtUrlCheck, HtmlUrlCheck, MarkdownComparator


class TestTxtUrlChecker(TestCase):

    def setUp(self):
        self.check = TxtUrlCheck()
        self.parser = MagicMock()

    def _check(self, mock_get, content, status_code):
        self.parser.parse.return_value = content
        mock_get.return_value.status_code = status_code

        return self.check.check(['dummy_path'], self.parser)

    @patch('validator.checks.read_content')
    @patch('requests.get')
    def test_happy_path(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa http://www.google.com aaa', 200)

        self.assertEqual({}, errors)

    @patch('validator.checks.read_content')
    @patch('requests.get')
    def test_not_found(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa http://www.google.com aaa', 404)

        self.assertIn('dummy_path', errors)
        self.assertEqual({'http://www.google.com': 404}, errors['dummy_path'].urls)

    @patch('validator.checks.read_content')
    @patch('requests.get')
    def test_retry_for_server_error(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa http://www.google.com aaa', 500)

        self.assertEqual(3, mock_get.call_count)

    @patch('validator.checks.read_content')
    @patch('requests.get')
    def test_make_only_one_request_per_unique_url(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa http://www.google.com aaa http://www.google.com aaa', 200)

        self.assertEqual(1, mock_get.call_count)

    @patch('validator.checks.read_content')
    @patch('requests.get')
    def test_skip_request_parameterized_urls(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa http://{{url}} aaa', 200)

        self.assertFalse(mock_get.called)

    @patch('validator.checks.read_content')
    @patch('requests.get')
    def test_skip_empty_urls(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa http:// aaa', 200)

        self.assertFalse(mock_get.called)

    @patch('validator.checks.read_content')
    @patch('requests.get')
    def test_skip_email(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa support@getkeepsafe.com aaa', 200)

        self.assertFalse(mock_get.called)


class TestHtmlUrlChecker(TestCase):

    def setUp(self):
        self.check = HtmlUrlCheck()
        self.parser = MagicMock()

    def _check(self, mock_get, content, status_code, check=None):
        check = check or self.check
        self.parser.parse.return_value = content
        mock_get.return_value.status_code = status_code

        return check.check(['dummy_path'], self.parser)

    @patch('validator.checks.read_content')
    @patch('requests.get')
    def test_happy_path(self, mock_get, mock_read):
        errors = self._check(mock_get, '<a href="http://www.google.com">link</a>', 200)

        mock_get.assert_called_with('http://www.google.com')
        self.assertEqual({}, errors)

    @patch('validator.checks.read_content')
    @patch('requests.get')
    def test_url_in_text_no_href(self, mock_get, mock_read):
        errors = self._check(mock_get, '<a>http://www.google.com</a>', 200)

        self.assertEqual({}, errors)

    @patch('validator.checks.read_content')
    @patch('requests.get')
    def test_add_http_if_missing(self, mock_get, mock_read):
        errors = self._check(mock_get, '<a href="www.google.com">link</a>', 200)

        self.assertEqual({}, errors)

    @patch('validator.checks.read_content')
    @patch('requests.get')
    def test_image(self, mock_get, mock_read):
        errors = self._check(mock_get, '<img src="http://www.google.com">', 200)

        self.assertTrue(mock_get.called)

    @patch('validator.checks.read_content')
    @patch('requests.get')
    def test_skip_request_parameterized_urls(self, mock_get, mock_read):
        errors = self._check(mock_get, '<a href="{{url}}">link</a>', 200)

        self.assertFalse(mock_get.called)

    @patch('validator.checks.read_content')
    @patch('requests.get')
    def test_skip_empty_urls(self, mock_get, mock_read):
        errors = self._check(mock_get, '<a href=""></a>', 200)

        self.assertFalse(mock_get.called)

    @patch('validator.checks.read_content')
    @patch('requests.get')
    def test_skip_email(self, mock_get, mock_read):
        errors = self._check(mock_get, '<a href="support@getkeepsafe.com"></a>', 200)

        self.assertFalse(mock_get.called)

    @patch('validator.checks.read_content')
    @patch('requests.get')
    def test_skip_images(self, mock_get, mock_read):
        check = HtmlUrlCheck(skip_images=True)
        errors = self._check(mock_get, '<img alt="image" src="http://no-image" />', 200, check)

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
