import re
import logging
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import defaultdict

from ..fs import Filetype, read_content
from ..model import Url


logging.getLogger('aiohttp').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)


class MissingValidatorError(Exception):
    pass


class TextUrlExtractor(object):

    def __init__(self, **kwargs):
        pass

    url_pattern = r"(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:[a-z]{2,13})/)(?:[^\s()<>\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\];:'\".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:[a-z]{2,13})\b/?(?!@)))"

    def _without_params(self, url):
        return not bool(re.search(r'\{\{\w+\}\}', url))

    def extract_urls(self, content):
        result = set(match.group().strip(').') for match in re.finditer(self.url_pattern, content))
        return filter(self._without_params, result)


class HtmlUrlExtractor(TextUrlExtractor):

    def __init__(self, root_url='', skip_images=False, **kwargs):
        self.root_url = root_url
        self.skip_images = skip_images

    def _validate_email(self, email):
    	if len(email) > 7:
    		if re.match('^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$', email):
    			return True
    	return False

    def _extract_from_anchors(self, soup):
        return set([a.get('href') or a.text for a in soup.find_all('a')])

    def _extract_from_img(self, soup):
        if self.skip_images:
            return set()
        return set([img.get('src') for img in soup.find_all('img')])

    def _fix_url(self, url):
        result = ''
        url_parsed = urlparse(url)
        if url_parsed.geturl().startswith('/'):
            if self.root_url:
                result = urljoin(self.root_url, url_parsed.geturl())
        elif url_parsed.scheme in ['http', 'https']:
            if re.match(self.url_pattern, url_parsed.geturl()):
                result = url_parsed.geturl()
        elif not url_parsed.scheme:
            if not self._validate_email(url_parsed.geturl()):
                full_url = 'http://' + url_parsed.geturl()
                if re.match(self.url_pattern, full_url):
                    result = full_url
        else:
            logging.error('{} not tested'.format(url_parsed.geturl()))
        return result

    def extract_urls(self, content):
        result = []
        soup = BeautifulSoup(content)
        urls = self._extract_from_anchors(soup) | self._extract_from_img(soup)
        for url in urls:
            fixed_url = self._fix_url(url)
            if fixed_url and self._without_params(fixed_url):
                result.append(fixed_url)
        return result


class UrlStatusChecker(object):
    retry_max_count = 3

    def _make_request(self, url):
        try:
            logging.info('checking {}'.format(url))
            res = yield from aiohttp.request('get', url)
            return res.status
        except Exception:
            logging.error('Error making request to %s', url)
            return 500

    def _retry_request(self, url, status):
        new_status = status
        times = 1
        while times < self.retry_max_count and status == new_status:
            new_status = yield from self._make_request(url)
            times = times + 1
        return new_status

    def _request_status_code(self, url):
        status = yield from self._make_request(url)
        if status == 500:
            return (yield from self._retry_request(url, status))
        return status

    def _is_valid(self, status_code):
        return 200 <= status_code < 300

    @asyncio.coroutine
    def _check_urls_coro(self, urls, future):
        for url in urls:
            url.status_code = yield from self._request_status_code(url.url)
        invalid_urls = filter(lambda u: not u.is_valid(), urls)
        future.set_result(list(invalid_urls))

    def check(self, urls):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        future = asyncio.Future()
        loop.run_until_complete(self._check_urls_coro(urls, future))
        loop.close()

        return future.result()

class UrlValidator(object):
    _extractors = {
        Filetype.txt: TextUrlExtractor,
        Filetype.html: HtmlUrlExtractor
    }

    def __init__(self, filetype, **kwargs):
        extractor_class = self._extractors.get(filetype)
        if extractor_class is None:
            raise MissingValidatorError('there is no validator for filetype %s', filetype)
        self.extractor = extractor_class(**kwargs)

    def check(self, paths, parser):
        flat_paths = set(p for sublist in paths for p in sublist)
        urls = {}
        for path in flat_paths:
            content = parser.parse(read_content(path))
            file_urls = self.extractor.extract_urls(content)
            for file_url in file_urls:
                url = urls.get(file_url, Url(file_url))
                url.add_file(path)
                urls[url.url] = url
        checker = UrlStatusChecker()
        invalid_urls = checker.check(urls.values())
        return invalid_urls
