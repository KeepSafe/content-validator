from enum import Enum
from bs4 import BeautifulSoup
import requests

from .result import ValidationError


class CheckType(Enum):
    link = 1
    structure = 2


class Check(object):

    def __init__(self, result, options={}):
        self.result = result
        self.options = options

    def set_original(self, original):
        self.original = original


class LinkCheck(Check):

    def _make_request(self, url):
        try:
            return requests.get(url).status_code
        except Error as e:
            logging.error(e)
            return 500

    def _retry_request(self, url, times=2, status=500):
        new_status = status
        while times > 0 and status == new_status:
            new_status = self._make_request(url)
            times = times - 1
        return 200 <= new_status < 300

    def _is_valid(self, url):
        status = self._make_request(url)
        if 200 <= status < 300:
            return True
        if status == 500:
            return self._retry_request(url)
        return False

    def check(self, content):
        soup = BeautifulSoup(content)
        links = soup.find_all('a')
        for link in links:
            url = link.get('href') or link.get_text()
            if not self._is_valid(url):
                self.result.errors.append(ValidationError('link {} invalid'.format(url)))


class StructureCheck(Check):

    def _clean_tree(self, tree):
        return tree

    def check(self, content):
        original_tree = BeautifulSoup(self.original)
        original_clean_tree = self._clean_tree(original_tree)
        content_tree = BeautifulSoup(content)
        content_clean_tree = self._clean_tree(content_tree)
        for o_node, c_node in zip(original_clean_tree, content_clean_tree):
            if o_node.name != c_node.name:
                self.result.errors.append(
                    ValidationError('original document has {} tag while {} tag in the other one'.format(o_node.name, c_node.name)))

        original_length = len(original_clean_tree.find_all())
        content_length = len(content_clean_tree.find_all())
        if original_length != content_length:
            self.result.errors.append(
                ValidationError('original document has {} tags while {} tag in the other one'.format(original_length, content_length)))


checkers = {
    CheckType.link: LinkCheck,
    CheckType.structure: StructureCheck
}


def check(check_type, result):
    return checkers[check_type](result)
