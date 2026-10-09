import re

from ..errors import MdDiff, ContentData

ARG_PATTERN = r'%(?:\d+\$)?(?:[a-zA-Z]+)?(?:\d+)?(?:.\d+)?[a-zA-Z]+'
REF_PATTERN = r'@string/\w+'


class JavaComparator:
    def _get_args(self, content):
        return re.findall(ARG_PATTERN, content)

    def _args_check(self, base, other):
        base_args = self._get_args(base)
        other_args = self._get_args(other)
        if len(base_args) != len(other_args):
            base_data = ContentData(base, base, '')
            other_data = ContentData(other, other, '')
            return MdDiff(base_data, other_data, 'java args do not match')
        return None

    def _ref_check(self, base, other):
        if self._has_ref(base):
            if not self._only_ref(base):
                base_data = ContentData(base, base, '')
                other_data = ContentData(other, other, '')
                return MdDiff(base_data, other_data, 'java args do not match')
            if not self._only_ref(other):
                base_data = ContentData(base, base, '')
                other_data = ContentData(other, other, '')
                return MdDiff(base_data, other_data, 'java args do not match')
        elif self._has_ref(other):
            base_data = ContentData(base, base, '')
            other_data = ContentData(other, other, '')
            return MdDiff(base_data, other_data, 'java args do not match')
        return None

    def _only_ref(self, content):
        return re.fullmatch(REF_PATTERN, content) is not None

    def _has_ref(self, content):
        return re.search(REF_PATTERN, content) is not None

    def check(self, data, parser, reader):
        data = data or []
        errors = []
        for row in data:
            row_items = list(map(str, row))
            base = row_items.pop(0)
            base_content = parser.parse(reader.read(base))
            for other in row_items:
                other_content = parser.parse(reader.read(other))
                ref_error = self._ref_check(base_content, other_content)
                if ref_error:
                    errors.append(ref_error)
                arg_error = self._args_check(base_content, other_content)
                if arg_error:
                    errors.append(arg_error)
        return errors
