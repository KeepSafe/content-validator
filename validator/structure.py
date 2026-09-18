"""Compare translated HTML or Markdown without constraining translated prose.

The command-line interface reads one JSON object from stdin and prints one JSON
object to stdout. A ``pairs`` array validates multiple documents in one process.
"""

from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
import json
import re
import sys


VOID = frozenset('area base br col embed hr img input link meta param source track wbr'.split())
BLOCK = frozenset(('address article aside blockquote body caption center dd details dialog div dl dt fieldset '
                   'figcaption figure footer form h1 h2 h3 h4 h5 h6 header hgroup hr html legend li main '
                   'menu nav ol p pre section summary table tbody td tfoot th thead tr ul').split())
TRANSLATABLE_ATTRS = frozenset(('alt', 'title', 'aria-label'))
TOKEN = re.compile(r'\{\{[^{}]+\}\}|\$\{[A-Za-z_][\w.-]*\}|\{[A-Za-z_][\w.-]*\}'
                   r'|%(?:\([A-Za-z_][\w.-]*\)|\d+\$)?[-+#0]*\d*(?:\.\d+)?'
                   r'(?:hh|ll|[hlLzjt])?[diouxXeEfFgGcrsa@]')
DIRECTIVE = re.compile(r'^\s*:::', re.MULTILINE)
SPACE = re.compile(r'\s+')


@dataclass
class _Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)


class _StrictHTML(HTMLParser):
    """Fragment parser that rejects common browser-repaired nesting and stray ends."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node('root')
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        self._start(tag, attrs, closed=False)

    def handle_startendtag(self, tag, attrs):
        self._start(tag, attrs, closed=True)

    def _start(self, tag, attrs, closed):
        if tag in VOID:
            closed = True
        elif closed:
            raise ValueError('self-closing non-void element <{}> is invalid HTML'.format(tag))
        ancestor_tags = [item.tag for item in self.stack]
        parent = self.stack[-1].tag
        if tag in BLOCK and 'p' in ancestor_tags:
            raise ValueError('block element <{}> inside <p> would be repaired'.format(tag))
        if tag == 'li' and parent not in ('ul', 'ol', 'menu'):
            raise ValueError('<li> must be inside a list')
        if tag in ('dt', 'dd') and parent != 'dl':
            raise ValueError('<{}> must be inside <dl>'.format(tag))
        if tag == 'tr' and parent not in ('table', 'thead', 'tbody', 'tfoot'):
            raise ValueError('<tr> must be inside a table section')
        if tag in ('td', 'th') and parent != 'tr':
            raise ValueError('<{}> must be inside <tr>'.format(tag))
        if tag in ('thead', 'tbody', 'tfoot', 'caption') and parent != 'table':
            raise ValueError('<{}> must be inside <table>'.format(tag))
        if tag == 'option' and parent not in ('select', 'optgroup', 'datalist'):
            raise ValueError('<option> must be inside a selection')
        if tag == 'a' and 'a' in ancestor_tags:
            raise ValueError('nested <a> would be repaired')
        if tag in ('button', 'form') and tag in ancestor_tags:
            raise ValueError('nested <{}> would be repaired'.format(tag))
        names = [name for name, _ in attrs]
        if len(names) != len(set(names)):
            raise ValueError('duplicate attribute on <{}>'.format(tag))
        node = _Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if not closed:
            self.stack.append(node)

    def handle_endtag(self, tag):
        if tag in VOID:
            raise ValueError('void element </{}> has a closing tag'.format(tag))
        if len(self.stack) == 1 or self.stack[-1].tag != tag:
            raise ValueError('unexpected </{}>; expected </{}>'.format(tag, self.stack[-1].tag))
        self.stack.pop()

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def handle_comment(self, data):
        # Comments cannot alter visible structure.
        pass

    def finish(self):
        self.close()
        if len(self.stack) != 1:
            raise ValueError('unclosed <{}>'.format(self.stack[-1].tag))
        return self.root


def _parse(content):
    parser = _StrictHTML()
    parser.feed(content)
    return parser.finish()


def _render(content, fmt, renderer):
    if not isinstance(content, str):
        raise ValueError('content must be a string')
    if fmt == 'html':
        return content
    if fmt != 'markdown':
        raise ValueError('format must be html or markdown')
    if renderer is None and DIRECTIVE.search(content):
        raise ValueError('Markdown ::: directives require an authoritative renderer')
    if renderer is not None:
        rendered = renderer(content)
    else:
        import markdown
        rendered = markdown.markdown(content, extensions=['tables', 'fenced_code'])
    if not isinstance(rendered, str):
        raise ValueError('Markdown renderer must return HTML as a string')
    return rendered


def _norm(text):
    return SPACE.sub(' ', text).strip()


def _text(node):
    return ''.join(child if isinstance(child, str) else _text(child) for child in node.children)


def _exact_text(node):
    parts = []
    for index, child in enumerate(node.children):
        if not isinstance(child, str):
            parts.append(_exact_text(child))
            continue
        if not child.strip():
            before = node.children[index - 1] if index else None
            after = node.children[index + 1] if index + 1 < len(node.children) else None
            before_is_block = before is None or isinstance(before, _Node) and before.tag in BLOCK
            after_is_block = after is None or isinstance(after, _Node) and after.tag in BLOCK
            if before_is_block and after_is_block:
                continue
        parts.append(child)
    return ''.join(parts)


def _attrs(node):
    attrs = dict(node.attrs)
    for name in TRANSLATABLE_ATTRS:
        attrs.pop(name, None)
    if 'class' in attrs and attrs['class'] is not None:
        attrs['class'] = tuple(sorted(attrs['class'].split()))
    return attrs


def _tokens(text):
    return Counter(TOKEN.findall(text))


def _element_children(node):
    return [child for child in node.children if isinstance(child, _Node)]


def _contains_block(node):
    return node.tag in BLOCK or any(_contains_block(child) for child in _element_children(node))


def _child_runs(node):
    """Keep blocks (including wrappers) ordered and bound inline movement between them."""
    blocks, runs = [], [[]]
    for child in _element_children(node):
        if _contains_block(child):
            blocks.append(child)
            runs.append([])
        else:
            runs[-1].append(child)
    return blocks, runs


def _signature(node, include_content=False):
    """Inline identity, independent of grammatical placement and translated text."""
    signature = (node.tag, tuple(sorted(_attrs(node).items())),
                 tuple(sorted((_signature(child, include_content) for child in _element_children(node)), key=repr)))
    if include_content:
        # Pair repeated tags by immutable content, even inside reordered wrappers.
        # Keep this separate from structural grouping so changes get precise errors.
        signature += (_text(node) if node.tag in ('pre', 'code') else '',
                      tuple((name, tuple(sorted(_tokens(node.attrs.get(name) or '').items())))
                            for name in sorted(TRANSLATABLE_ATTRS)))
    return signature


def _path(path, node, index):
    return '{}/{}[{}]'.format(path, node.tag, index)


def _error(errors, code, path, message):
    errors.append({'code': code, 'path': path, 'message': message})


def _compare(source, target, path, errors, preserve_text):
    if source.tag != target.tag:
        _error(errors, 'tag', path, 'expected <{}>, found <{}>'.format(source.tag, target.tag))
        return
    if _attrs(source) != _attrs(target):
        _error(errors, 'attribute', path, 'protected attributes differ')
    if preserve_text and source.attrs != target.attrs:
        _error(errors, 'attribute', path, 'attributes differ in exact-content mode')
    for name in TRANSLATABLE_ATTRS:
        if (name in source.attrs) != (name in target.attrs):
            _error(errors, 'attribute', path, '{} presence differs'.format(name))
        elif name in source.attrs:
            if _tokens(source.attrs[name] or '') != _tokens(target.attrs[name] or ''):
                _error(errors, 'placeholder', path, '{} placeholder identities or counts differ'.format(name))
            if source.attrs[name] and not (target.attrs[name] or '').strip():
                _error(errors, 'text', path, '{} text was erased'.format(name))
    if source.tag in ('pre', 'code') and _text(source) != _text(target):
        _error(errors, 'code', path, 'code content differs')
    if source.tag == 'root' or source.tag in BLOCK:
        if _tokens(_text(source)) != _tokens(_text(target)):
            _error(errors, 'placeholder', path, 'protected placeholder identities or counts differ')
    if _norm(_text(source)) and not _norm(_text(target)):
        _error(errors, 'text', path, 'visible text was erased')
    if 'tab-label' in (source.attrs.get('class') or '').split():
        label = _norm(_text(source))
        if label in ('iOS', 'Android') and label != _norm(_text(target)):
            _error(errors, 'platform_label', path, 'platform tab label changed')
    if preserve_text and _norm(_exact_text(source)) != _norm(_exact_text(target)):
        _error(errors, 'text', path, 'visible text differs')

    source_blocks, source_runs = _child_runs(source)
    target_blocks, target_runs = _child_runs(target)
    if len(source_blocks) != len(target_blocks):
        _error(errors, 'structure', path, 'number of block elements differs')
    for index, (left, right) in enumerate(zip(source_blocks, target_blocks), 1):
        _compare(left, right, _path(path, left, index), errors, preserve_text)

    for source_inline, target_inline in zip(source_runs, target_runs):
        source_groups = {}
        target_groups = {}
        for child in source_inline:
            source_groups.setdefault(repr(_signature(child)), []).append(child)
        for child in target_inline:
            target_groups.setdefault(repr(_signature(child)), []).append(child)
        if Counter({key: len(value) for key, value in source_groups.items()}) != Counter(
                {key: len(value) for key, value in target_groups.items()}):
            _error(errors, 'structure', path, 'inline element tags, nesting, or protected attributes differ')
        for key in sorted(source_groups.keys() & target_groups.keys()):
            left_group = sorted(source_groups[key], key=lambda node: repr(_signature(node, include_content=True)))
            right_group = sorted(target_groups[key], key=lambda node: repr(_signature(node, include_content=True)))
            for index, (left, right) in enumerate(zip(left_group, right_group), 1):
                _compare(left, right, _path(path, left, index), errors, preserve_text)


def validate_structure(source, target, source_format='html', target_format='html',
                       markdown_renderer=None, preserve_text=False):
    """Return ``{'ok': bool, 'errors': [{code, path, message}, ...]}``.

    ``markdown_renderer`` accepts Markdown text and returns rendered HTML. Supply
    the publishing renderer for custom Markdown syntax. ``preserve_text`` is for
    migration parity; ordinary translation checks leave prose translatable.
    """
    errors = []
    try:
        source_dom = _parse(_render(source, source_format, markdown_renderer))
    except (ValueError, TypeError) as exc:
        _error(errors, 'parse', 'source', str(exc))
        return {'ok': False, 'errors': errors}
    try:
        target_dom = _parse(_render(target, target_format, markdown_renderer))
    except (ValueError, TypeError) as exc:
        _error(errors, 'parse', 'target', str(exc))
        return {'ok': False, 'errors': errors}
    _compare(source_dom, target_dom, '', errors, preserve_text)
    return {'ok': not errors, 'errors': errors}


def main():
    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict):
            raise ValueError('request must be a JSON object')
        if 'pairs' in request:
            if not isinstance(request['pairs'], list):
                raise ValueError('pairs must be an array')
            results = []
            for pair in request['pairs']:
                if not isinstance(pair, dict):
                    raise ValueError('each pair must be an object')
                result = validate_structure(pair.get('source'), pair.get('target'),
                                            pair.get('source_format', 'html'),
                                            pair.get('target_format', 'html'),
                                            preserve_text=pair.get('preserve_text', False))
                results.append({'id': pair.get('id'), **result})
            response = {'ok': all(result['ok'] for result in results), 'results': results}
        else:
            response = validate_structure(request.get('source'), request.get('target'),
                                          request.get('source_format', 'html'),
                                          request.get('target_format', 'html'),
                                          preserve_text=request.get('preserve_text', False))
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        response = {'ok': False, 'errors': [{'code': 'input', 'path': '', 'message': str(exc)}]}
    json.dump(response, sys.stdout, ensure_ascii=False)
    sys.stdout.write('\n')
    return 0 if response['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
