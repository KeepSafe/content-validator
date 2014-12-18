from enum import Enum
from bs4 import BeautifulSoup
from itertools import zip_longest
import requests


class ValidationError(object):

    def __init__(self):
        self.errors = []

    def __bool__(self):
        return len(self.errors) > 0

    def add_error(self, error):
        self.errors.append(error)

    def __str__(self):
        return '\n'.join([str(error) for error in self.errors])


class ContentError(ValidationError):

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def __str__(self):
        msg = 'Errors for file {}\n'.format(self.file_path)
        msg = msg + super().__str__()
        return msg


class LinkError(object):

    def __init__(self, url, status_code):
        self.url = url
        self.status_code = status_code

    def __str__(self):
        return '\t{} returned status code {}'.format(self.url, self.status_code)


class CompareError(ValidationError):

    def __init__(self, base_file_path, other_file_path):
        super().__init__()
        self.base_file_path = base_file_path
        self.other_file_path = other_file_path

    def __str__(self):
        msg = 'Errors for files comparison between base file {} and other file {}\n'.format(
            self.base_file_path, self.other_file_path)
        msg = msg + super().__str__()
        return msg


class TagNameError(object):

    def __init__(self, base_tag_name, other_tag_name):
        self.base_tag_name = base_tag_name
        self.other_tag_name = other_tag_name

    def __str__(self):
        return '\tTag {} in base file corresponds to {} in the other file'.format(self.base_tag_name, self.other_tag_name)


class MissingTagError(object):

    def __init__(self, tag_name, file_path):
        self.tag_name = tag_name
        self.file_path = file_path

    def __str__(self):
        return '\tTag {} is missing from {}'.format(self.tag_name, self.file_path)


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
        # TODO clean tree
        return soup

    def compare(self, parser, base_file_path, other_file_path):
        base_content = parser.parse(base_file_path)
        other_content = parser.parse(other_file_path)
        base_tree = self._build_tree(base_content)
        other_tree = self._build_tree(other_content)
        error = CompareError(base_file_path, other_file_path)
        for base_node, other_node in zip_longest(base_tree.descendants, other_tree.descendants):
            if base_node is None and other_node is not None and other_node.name is not None:
                error.add_error(MissingTagError(other_node.name, base_file_path))
            elif other_node is None and base_node is not None and base_node.name is not None:
                error.add_error(MissingTagError(base_node.name, other_file_path))
            elif other_node is not None and base_node is not None and base_node.name != other_node.name:
                error.add_error(TagNameError(base_node.name, other_node.name))
        return error


def check_links():
    return LinkCheck()


def check_structure():
    return StructureCheck()
