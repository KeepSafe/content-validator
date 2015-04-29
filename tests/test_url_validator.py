from unittest import TestCase
from unittest.mock import patch, MagicMock
from . import AsyncTestCase

from validator.checks import urls
from validator.fs import Filetype

class TestTxtUrlChecker(AsyncTestCase):

    def setUp(self):
        super().setUp()
        self.check = urls(Filetype.txt)
        self.parser = MagicMock()

    def _check(self, mock_get, content, status_code):
        self.parser.parse.return_value = content
        res = MagicMock()
        res.status = status_code
        mock_get.return_value = self.make_fut(res)

        return self.check.check([['dummy_path']], self.parser)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_happy_path(self, mock_get, mock_read):
        invalid_urls = self._check(mock_get, 'aaa http://www.google.com aaa', 200)

        self.assertEqual([], invalid_urls)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_not_found(self, mock_get, mock_read):
        invalid_urls = self._check(mock_get, 'aaa http://www.google.com aaa', 404)

        self.assertEqual(1, len(invalid_urls))
        url = invalid_urls[0]
        self.assertEqual('http://www.google.com', url.url)
        self.assertEqual(['dummy_path'], url.files)
        self.assertEqual(404, url.status_code)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_retry_for_server_error(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa http://www.google.com aaa', 500)

        self.assertEqual(3, mock_get.call_count)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_make_only_one_request_per_unique_url(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa http://www.google.com aaa http://www.google.com aaa', 200)

        self.assertEqual(1, mock_get.call_count)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_skip_parameterized_urls_in_middle(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa http://domain.com/{{param}} aaa', 200)

        self.assertFalse(mock_get.called)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_skip_parameterized_urls_from_start(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa http://{{ticket.url}}, aaa', 200)

        self.assertFalse(mock_get.called)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_include_params_in_the_url(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa http://domain.com/hello?id=123 aaa', 200)

        mock_get.assert_called_with('get', 'http://domain.com/hello?id=123')

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_skip_empty_urls(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa http:// aaa', 200)

        self.assertFalse(mock_get.called)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_skip_email(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa support@getkeepsafe.com aaa', 200)

        self.assertFalse(mock_get.called)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_skip_commas(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa http://{{ticket.url}}, aaa', 404)

        self.assertFalse(mock_get.called)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_skip_commas(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa http://www.google.com, aaa', 200)

        mock_get.assert_called_with('get', 'http://www.google.com')

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_skip_commas(self, mock_get, mock_read):
        errors = self._check(mock_get, 'aaa http://bit.ly/UpdateKeepSafe。拥有最新版本就能解决大部分问题了。 aaa', 200)

        mock_get.assert_called_with('get', 'http://bit.ly/UpdateKeepSafe')


class TestHtmlUrlChecker(AsyncTestCase):

    def setUp(self):
        super().setUp()
        self.check = urls(Filetype.html)
        self.parser = MagicMock()

    def _check(self, mock_get, content, status_code, check=None):
        check = check or self.check
        self.parser.parse.return_value = content
        res = MagicMock()
        res.status = status_code
        mock_get.return_value = self.make_fut(res)

        return check.check(['dummy_path'], self.parser)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_happy_path(self, mock_get, mock_read):
        errors = self._check(mock_get, '<a href="http://www.google.com">link</a>', 200)

        mock_get.assert_called_with('get', 'http://www.google.com')
        self.assertEqual([], errors)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_url_in_text_no_href(self, mock_get, mock_read):
        errors = self._check(mock_get, '<a>http://www.google.com</a>', 200)

        self.assertEqual([], errors)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_add_http_if_missing(self, mock_get, mock_read):
        errors = self._check(mock_get, '<a href="www.google.com">link</a>', 200)

        self.assertEqual([], errors)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_image(self, mock_get, mock_read):
        errors = self._check(mock_get, '<img src="http://www.google.com">', 200)

        self.assertTrue(mock_get.called)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_skip_request_parameterized_urls(self, mock_get, mock_read):
        errors = self._check(mock_get, '<a href="{{url}}">link</a>', 200)

        self.assertFalse(mock_get.called)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_skip_empty_urls(self, mock_get, mock_read):
        errors = self._check(mock_get, '<a href=""></a>', 200)

        self.assertFalse(mock_get.called)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_skip_email(self, mock_get, mock_read):
        errors = self._check(mock_get, '<a href="support@getkeepsafe.com"></a>', 200)

        self.assertFalse(mock_get.called)

    @patch('validator.checks.url_validator.read_content')
    @patch('aiohttp.request')
    def test_skip_images(self, mock_get, mock_read):
        check = urls(Filetype.html, skip_images=True)
        errors = self._check(mock_get, '<img alt="image" src="http://no-image" />', 200, check)

        self.assertFalse(mock_get.called)
