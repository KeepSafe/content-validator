import re

from ..errors import MdDiff

ARG_PATTERN = r'%(?:\d+\$)?(?:[a-zA-Z]+)?(?:\d+)?(?:.\d+)?[a-zA-Z]+'
REF_PATTERN = r'@string/\w+'


class JavaComparator(object):
    def _get_args(self, content):
        return re.findall(ARG_PATTERN, content)

    def _args_check(self, base, other):
        base_args = self._get_args(base)
        other_args = self._get_args(other)
        if len(base_args) != len(other_args):
            return MdDiff(base, other, 'java args do not match')
        return None

    def _ref_check(self, base, other):
        if self._has_ref(base):
            if not self._only_ref(base):
                return MdDiff(base, other, 'java args do not match')
            if not self._only_ref(other):
                return MdDiff(base, other, 'java args do not match')
        elif self._has_ref(other):
            return MdDiff(base, other, 'java args do not match')
        return None

    def _only_ref(self, content):
        return re.fullmatch(REF_PATTERN, content) is not None

    def _has_ref(self, content):
        return re.search(REF_PATTERN, content) is not None

    def check(self, data, parser):
        if not data:
            return []
        errors = []
        for row in data:
            base = row.pop(0)
            base_content = parser.parse(base)
            for other in row:
                other_content = parser.parse(other)
                ref_error = self._ref_check(base_content, other_content)
                if ref_error:
                    errors.append(ref_error)
                arg_error = self._args_check(base_content, other_content)
                if arg_error:
                    errors.append(arg_error)
        return errors
