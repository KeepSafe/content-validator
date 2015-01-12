import difflib

class TxtDiffer(object):
    def diff(self, base, other):
        differ = difflib.Differ()
        diff = list(differ.compare(base.splitlines(keepends=True), other.splitlines(keepends=True)))
        return '\n'.join(diff)
