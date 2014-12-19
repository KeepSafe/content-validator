from enum import Enum
from bs4 import BeautifulSoup
from itertools import zip_longest
import requests

from .errors import LinkError, TagsCountError, TagNameError, ContentError, CompareError, MissingFileError
from .utils import clean_html_tree


class ContentCheck(object):

    def validate(parser, file_path):
        pass


class CompareCheck(object):

    def compare(self, parser, base_file_path, other_file_path):
        pass


class LinkCheck(ContentCheck):
    retry_max_count = 3

    def _make_request(self, url):
        try:
            return requests.get(url).status_code
        except Error as e:
            logging.error(e)
            return 500

    def _retry_request(self, url, status):
        new_status = status
        times = 1
        while times < self.retry_max_count and status == new_status:
            new_status = self._make_request(url)
            times = times + 1
        return new_status

    def _url_status_code(self, url):
        status = self._make_request(url)
        if status == 500:
            return self._retry_request(url, status)
        return status

    def validate(self, parser, file_path):
        content = parser.parse(file_path)
        soup = BeautifulSoup(content)
        links = soup.find_all('a')
        error = ContentError(file_path)
        for link in links:
            url = link.get('href') or link.get_text()
            status_code = self._url_status_code(url)
            if not 200 <= status_code < 300:
                error.add_error(LinkError(url, status_code))
        return error


class StructureCheck(CompareCheck):

    def _build_tree(self, content):
        soup = BeautifulSoup(content)
        clean_soup = clean_html_tree(soup)
        return clean_soup

    def compare(self, parser, base_file_path, other_file_path):
        error = CompareError(base_file_path, other_file_path)

        base_content = parser.parse(base_file_path)
        other_content = parser.parse(other_file_path)
        if not other_content:
            error.add_error(MissingFileError(other_file_path))
            return error

        base_tree = self._build_tree(base_content)
        other_tree = self._build_tree(other_content)
        for base_node, other_node in zip(base_tree.descendants, other_tree.descendants):
            if base_node.name != other_node.name:
                error.add_error(TagNameError(base_node.name, other_node.name))

        base_tags_count = len(base_tree.find_all())
        other_tags_count = len(other_tree.find_all())
        if base_tags_count != other_tags_count:
            error.add_error(TagsCountError(base_tags_count, other_tags_count))

        return error


def check_links():
    return LinkCheck()


def check_structure():
    return StructureCheck()
