from unittest import TestCase
from unittest.mock import patch, MagicMock
from .. import url


class TestUrls(TestCase):
    def _run_filter_invalid_urls(self, http_code):
        res = MagicMock()
        res.status_code = http_code
        with patch('requests.get') as mock_req:
            mock_req.return_value = res
            return url._filter_invalid_urls(['dummy'])

    def test_filter_invalid_urls_success_status(self):
        for code in [200, 201]:
            actual = self._run_filter_invalid_urls(code)
            self.assertEqual({'dummy'}, actual)

    def test_filter_invalid_urls_fail_status(self):
        for code in [400, 404, 500]:
            actual = self._run_filter_invalid_urls(code)
            self.assertEqual({}, actual)

    def test_retries_tree_times_for_500(self):
        res = MagicMock()
        res.status_code = 500
        with patch('requests.get') as mock_req:
            mock_req.return_value = res
            url._filter_invalid_urls(['dummy'])
            self.assertEqual(3, mock_req.call_count)

    def test_urls_from_content_happy_path(self):
        content = """
            This is an automatic reply to let you know that we have received your message.
            Your ticket number is: {{ticket.id}}
            {{dc.auto_reply_placeholder-thumbnail_problem}}
            You can check our Knowledge Base here: http://support.getkeepsafe.com/hc/en-us
            If you have an issue with KeepSafe, please check our Known issues section here: http://support.getkeepsafe.com/hc/en-us/sections/200099945-Known-problems
            Forgot your PIN? {{dc.url_tutorial}}#pin-reminder
            Due to a high amount of support enquiries, we are unable to personally reply to your initial message; however, if  this does not solve the issue, please reply to this email with a more detailed description and our support team will help you further..
            Our support team is here to help every day, Monday through Friday.
            Thank you,
            The KeepSafe Team"
        """
        expected = {
            'http://support.getkeepsafe.com/hc/en-us',
            'http://support.getkeepsafe.com/hc/en-us/sections/200099945-Known-problems'
        }
        actual = url._urls_from_content(content)
        self.assertEqual(expected, actual)

    def test_urls_from_content_dont_duplicate_urls(self):
        content = """
            http://support.getkeepsafe.com/hc/en-us
            http://support.getkeepsafe.com/hc/en-us
        """
        expected = {
            'http://support.getkeepsafe.com/hc/en-us'
        }
        actual = url._urls_from_content(content)
        self.assertEqual(expected, actual)

    def test_filter_invalid_urls_happy_path(self):
        urls = ['dummy']
        with patch('url_validator._is_url_valid') as mock_valid:
            mock_valid.return_value = True
            invalid_urls = url._filter_invalid_urls(urls)
            self.assertEqual({}, invalid_urls)
