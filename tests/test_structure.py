import json
from pathlib import Path
import subprocess
import sys

import pytest

from validator.structure import validate_structure


def codes(result):
    return {error['code'] for error in result['errors']}


def test_translation_can_reorder_inline_markup_and_translate_accessible_text():
    source = '<p>Hello <a href="/help" title="Help">friend</a> and <strong>all</strong>.</p>'
    target = '<p><strong>Alle</strong> und <a title="Hilfe" href="/help">Freunde</a>, hallo.</p>'
    assert validate_structure(source, target) == {'ok': True, 'errors': []}


@pytest.mark.parametrize('target', [
    '<p>Hallo <a href="/other">Hilfe</a>.</p>',
    '<p>Hallo <a href="/help" id="new">Hilfe</a>.</p>',
    '<p>Hallo <a href="/help" class="new">Hilfe</a>.</p>',
    '<p>Hallo <a href="/help" data-kind="new">Hilfe</a>.</p>',
])
def test_protected_attributes_cannot_change(target):
    source = '<p>Hello <a href="/help">help</a>.</p>'
    assert not validate_structure(source, target)['ok']


def test_duplicate_link_or_inline_element_is_rejected():
    source = '<p><a href="/help">Help</a></p>'
    target = '<p><a href="/help">Hilfe</a><a href="/help">Hilfe</a></p>'
    assert 'structure' in codes(validate_structure(source, target))


def test_ordered_block_tree_and_table_cells_are_preserved():
    source = '<h2>Start</h2><table><tr><th>Name</th><td>Value</td></tr></table>'
    target = '<table><tr><td>Wert</td><th>Name</th></tr></table><h2>Anfang</h2>'
    assert 'tag' in codes(validate_structure(source, target))
    cells = validate_structure('<table><tr><td>A</td><td>B</td></tr></table>',
                               '<table><tr><td>A</td></tr></table>')
    assert 'structure' in codes(cells)


def test_tab_group_and_platform_label_are_protected():
    source = '<div class="tabs"><div class="tab" data-tab="ios"><h1 class="tab-label">iOS</h1><p>Open</p></div>' \
             '<div class="tab" data-tab="android"><h1 class="tab-label">Android</h1><p>Tap</p></div></div>'
    changed = source.replace('iOS</h1>', 'iPhone</h1>')
    assert 'platform_label' in codes(validate_structure(source, changed))
    assert 'attribute' in codes(validate_structure(source, source.replace('data-tab="ios"', 'data-tab="android"', 1)))
    missing = source.replace('<div class="tab" data-tab="android"><h1 class="tab-label">Android</h1>'
                             '<p>Tap</p></div>', '')
    assert 'structure' in codes(validate_structure(source, missing))


@pytest.mark.parametrize('target', [
    '<p>Bonjour {{name}}; {count} éléments et %1$s.</p>',
    '<p>Bonjour {{user}}; {count} éléments et %1$s.</p>',
    '<p>Bonjour {{name}}; {count} éléments et %2$s.</p>',
])
def test_placeholder_identity_and_count_per_block(target):
    source = '<p>Hello {{name}}, {{name}}; {count} items and %1$s.</p>'
    result = validate_structure(source, target)
    assert result['ok'] == (target.count('{{name}}') == 2)
    if not result['ok']:
        assert 'placeholder' in codes(result)


def test_moving_token_between_paragraphs_is_rejected():
    source = '<p>Hello {{name}}</p><p>Continue</p>'
    target = '<p>Bonjour</p><p>Continuer {{name}}</p>'
    assert 'placeholder' in codes(validate_structure(source, target))


def test_placeholder_can_move_within_one_block_but_not_disappear_from_accessible_text():
    source = '<p><a href="/x">{{name}}</a> says hello.</p>'
    target = '<p>{{name}} sagt <a href="/x">Hallo</a>.</p>'
    assert validate_structure(source, target)['ok']
    source = '<p><img src="/x" alt="Photo of {{name}}">Hello</p>'
    target = '<p><img src="/x" alt="Foto">Hallo</p>'
    assert 'placeholder' in codes(validate_structure(source, target))


def test_code_and_erased_prose_are_rejected():
    assert 'code' in codes(validate_structure('<pre><code>print(1)</code></pre>',
                                              '<pre><code>print(2)</code></pre>'))
    assert 'text' in codes(validate_structure('<p>Do this</p>', '<p>   </p>'))
    assert 'text' in codes(validate_structure('<p><a href="/x">Help</a></p>',
                                              '<p><a href="/x"></a></p>'))
    assert 'text' in codes(validate_structure('<p>Emphasize <em>this</em></p>',
                                              '<p>Emphase <em></em></p>'))
    assert 'text' in codes(validate_structure('Hello', ''))


def test_percentage_in_prose_is_not_mistaken_for_a_placeholder():
    assert validate_structure('<p>25% off</p>', '<p>25% Rabatt</p>')['ok']


@pytest.mark.parametrize('html', [
    '<p>Open', '<p><b>Text</p></b>', '<p>Text</div>', '<p>Text</p></p>',
    '<p>Text<div>Other</div></p>', '<ul><li>First<li>Second</li></ul>',
    '<table><tr><td>A<td>B</td></tr></table>', '<a href="/x"><a href="/y">B</a></a>',
    '<div id="a" id="b"></div>', '<p/>',
])
def test_malformed_html_is_rejected_without_browser_repair(html):
    result = validate_structure(html, '<p>Valid</p>')
    assert 'parse' in codes(result)


def test_void_elements_and_unicode_are_accepted():
    source = '<p>Résumé <img src="/a.png" alt="Photo"><br>Done</p>'
    target = '<p>Zusammenfassung <img alt="Bild" src="/a.png"/><br/>Fertig</p>'
    assert validate_structure(source, target)['ok']


def test_markdown_to_html_and_custom_directives():
    source = 'Hello [friend](/help).'
    target = '<p>Hallo <a href="/help">Freund</a>.</p>'
    assert validate_structure(source, target, source_format='markdown')['ok']
    assert validate_structure(source, 'Hallo [Freund](/help).', source_format='markdown',
                              target_format='markdown')['ok']
    directive = '::: note\nHello\n:::'
    assert 'parse' in codes(validate_structure(directive, '<aside>Hello</aside>', source_format='markdown'))

    def renderer(markdown_text):
        assert markdown_text == directive
        return '<aside><p>Hello</p></aside>'

    assert validate_structure(directive, '<aside><p>Hallo</p></aside>',
                              source_format='markdown', markdown_renderer=renderer)['ok']


def test_preserve_text_allows_formatting_whitespace_but_rejects_changed_prose_or_alt():
    source = '<div>\n<p>Hello <strong>friend</strong></p>\n<p>Next</p>\n</div>'
    same = '<div><p>Hello <strong>friend</strong></p><p>Next</p></div>'
    assert validate_structure(source, same, preserve_text=True)['ok']
    assert 'text' in codes(validate_structure(source, same.replace('friend', 'Freund'), preserve_text=True))
    assert 'attribute' in codes(validate_structure('<img src="/x" alt="Picture">',
                                                   '<img src="/x" alt="Bild">', preserve_text=True))
    assert 'attribute' in codes(validate_structure('<p class="a b">Text</p>',
                                                   '<p class="b a">Text</p>', preserve_text=True))


def test_standalone_cli_single_and_batch():
    script = Path(__file__).resolve().parents[1] / 'validator' / 'structure.py'
    request = {'pairs': [
        {'id': 'good', 'source': '<p>Hi</p>', 'target': '<p>Hallo</p>'},
        {'id': 'bad', 'source': '<p>Hi</p>', 'target': '<h2>Hallo</h2>'},
    ]}
    completed = subprocess.run([sys.executable, str(script)], input=json.dumps(request),
                               text=True, capture_output=True, check=False)
    response = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert response['ok'] is False
    assert [(item['id'], item['ok']) for item in response['results']] == [('good', True), ('bad', False)]
    assert not completed.stderr


@pytest.mark.parametrize('wrapper', ['<a href="/x">{}</a>', '<a href="/x"><span>{}</span></a>'])
def test_block_wrappers_keep_their_place_in_document_order(wrapper):
    source = wrapper.format('<h2>Title</h2>') + '<p>Body</p>'
    translated = wrapper.format('<h2>Titel</h2>')
    assert validate_structure(source, translated + '<p>Text</p>')['ok']
    assert not validate_structure(source, '<p>Text</p>' + translated)['ok']


def test_inline_elements_cannot_cross_a_block_boundary():
    source = '<div><a href="/x">Help</a><p>Body</p></div>'
    assert validate_structure(source, '<div><a href="/x">Hilfe</a><p>Text</p></div>')['ok']
    assert not validate_structure(source, '<div><p>Text</p><a href="/x">Hilfe</a></div>')['ok']


@pytest.mark.parametrize('attribute', ['alt', 'title', 'aria-label'])
def test_attribute_placeholders_cannot_move_into_prose(attribute):
    source = '<p><img src="/x" {}="Photo {{{{name}}}}">Hello</p>'.format(attribute)
    target = '<p><img src="/x" {}="Foto">Hallo {{{{name}}}}</p>'.format(attribute)
    assert 'placeholder' in codes(validate_structure(source, target))
    translated = '<p><img src="/x" {}="Foto {{{{name}}}}">Hallo</p>'.format(attribute)
    assert validate_structure(source, translated)['ok']


def test_placeholders_cannot_move_between_attributes_or_elements():
    source = '<p><img src="/x" alt="Photo {{name}}" title="Photo {{count}}"></p>'
    target = '<p><img src="/x" alt="Foto {{count}}" title="Foto {{name}}"></p>'
    assert 'placeholder' in codes(validate_structure(source, target))
    source = '<p><img src="/x" alt="Photo {{name}}"><img src="/y" alt="Photo {{count}}"></p>'
    target = '<p><img src="/x" alt="Foto {{count}}"><img src="/y" alt="Foto {{name}}"></p>'
    assert 'placeholder' in codes(validate_structure(source, target))


@pytest.mark.parametrize('wrapper', ['{}', '<strong>{}</strong>'])
def test_inline_code_can_reorder_without_changing_content(wrapper):
    foo = wrapper.format('<code>foo</code>')
    bar = wrapper.format('<code>bar</code>')
    source = '<p>Use {} before {}</p>'.format(foo, bar)
    target = '<p>Vor {} nutze {}</p>'.format(bar, foo)
    assert validate_structure(source, target)['ok']
    assert not validate_structure(source, target.replace('foo', 'baz'))['ok']
    assert not validate_structure(source, target.replace('foo', 'bar'))['ok']
    assert not validate_structure(source, target, preserve_text=True)['ok']


def test_repeated_inline_elements_match_their_attribute_placeholders_when_reordered():
    source = '<p><img src="/x" alt="Photo {{name}}"><img src="/x" alt="Photo {{count}}"></p>'
    target = '<p><img src="/x" alt="Foto {{count}}"><img src="/x" alt="Foto {{name}}"></p>'
    assert validate_structure(source, target)['ok']
    assert not validate_structure(source, target.replace('{{name}}', '{{count}}'))['ok']


def test_markdown_inline_code_reordering():
    assert validate_structure('Use `foo` before `bar`.', 'Vor `bar` nutze `foo`.',
                              source_format='markdown', target_format='markdown')['ok']


def test_cli_translation_contract_accepts_reordering_and_rejects_corruption():
    script = Path(__file__).resolve().parents[1] / 'validator' / 'structure.py'
    source_code = '<p>Use <code>foo</code> before <code>bar</code></p>'
    reordered_code = '<p>Vor <code>bar</code> nutze <code>foo</code></p>'
    pairs = [
        {'id': 'grammar', 'source': source_code, 'target': reordered_code},
        {'id': 'duplicate-code', 'source': source_code, 'target': reordered_code.replace('foo', 'bar')},
        {'id': 'block-order', 'source': '<a href="/x"><h2>Title</h2></a><p>Body</p>',
         'target': '<p>Text</p><a href="/x"><h2>Titel</h2></a>'},
        {'id': 'attribute-token', 'source': '<p><img src="/x" alt="Photo {{name}}">Hello</p>',
         'target': '<p><img src="/x" alt="Foto">Hallo {{name}}</p>'},
    ]
    for request, expected in [({'pairs': pairs}, False), (pairs[0], True)]:
        completed = subprocess.run([sys.executable, str(script)], input=json.dumps(request),
                                   text=True, capture_output=True, check=False)
        response = json.loads(completed.stdout)
        assert response['ok'] is expected
        assert completed.returncode == (0 if expected else 1)
        assert not completed.stderr
        if 'pairs' in request:
            assert [(item['id'], item['ok']) for item in response['results']] == [
                ('grammar', True), ('duplicate-code', False), ('block-order', False), ('attribute-token', False),
            ]
            for result in response['results'][1:]:
                assert result['errors']
                assert all({'code', 'path', 'message'} <= error.keys() for error in result['errors'])


@pytest.mark.parametrize('source,target,ok', [
    ('%s', '%%s', False), ('%%s', '%s', False), ('%%s', '%%d', True),
    ('%%%s', '%s', True), ('%%%%s', 'literal', True),
    ('%1$s', '%%1$s', False), ('%(name)s', '%%(name)s', False),
])
def test_printf_escapes_are_not_substitutions(source, target, ok):
    assert validate_structure('<p>' + source + '</p>', '<p>' + target + '</p>')['ok'] is ok


@pytest.mark.parametrize('attribute', ['title', 'alt', 'aria-label'])
def test_reordered_inline_elements_match_attribute_presence(attribute):
    source = '<p><a href="/x" {}="Help">Help</a><a href="/x">More</a></p>'.format(attribute)
    target = '<p><a href="/x">Mehr</a><a href="/x" {}="Hilfe">Hilfe</a></p>'.format(attribute)
    assert validate_structure(source, target)['ok']
    assert not validate_structure(source, target.replace(' {}="Hilfe"'.format(attribute), ''))['ok']


@pytest.mark.parametrize('example', [
    '```text\n::: note\nHello\n:::\n```',
    '~~~text\n::: note\nHello\n:::\n~~~',
    '    ::: note\n    Hello\n    :::',
    '`example\n::: note`',
])
def test_literal_markdown_directives_in_code_are_accepted(example):
    source = 'Example:\n\n' + example
    target = 'Beispiel:\n\n' + example
    assert validate_structure(source, target, source_format='markdown', target_format='markdown')['ok']
    assert not validate_structure(source + '\n\n::: note', target,
                                  source_format='markdown', target_format='markdown')['ok']


@pytest.mark.parametrize('elements', [
    ['<span></span>', '<span>Hello</span>'],
    ['<a href="/x" title="">Help</a>', '<a href="/x" title="Help">Help</a>'],
    ['<strong><span></span></strong>', '<strong><span>Hello</span></strong>'],
])
def test_reordering_preserves_empty_and_nonempty_inline_content(elements):
    source = '<p>' + ''.join(elements) + '</p>'
    target = '<p>' + ''.join(reversed(elements)) + '</p>'
    assert validate_structure(source, target)['ok']
    assert not validate_structure(source, '<p>' + elements[0] * 2 + '</p>')['ok']


@pytest.mark.parametrize('source,target', [
    ('<p>Save 25%</p><p>off everything</p>', '<p>Spare 25%</p><p>auf alles</p>'),
    ('<p>{</p><p>name}</p>', '<p>{</p><p>Name}</p>'),
    ('<div>{{<p>example</p>name}}</div>', '<div>{{<p>Beispiel</p>Name}}</div>'),
    ('<a href="/x"><p>Save 25%</p></a><p>off everything</p>',
     '<a href="/x"><p>Spare 25%</p></a><p>auf alles</p>'),
])
def test_placeholder_scanning_does_not_join_separate_blocks(source, target):
    assert validate_structure(source, target)['ok']


def test_real_placeholders_in_wrapped_blocks_remain_protected():
    source = '<a href="/x"><p>Hello {{name}}</p></a><p>Next</p>'
    assert validate_structure(source, source.replace('Hello', 'Hallo'))['ok']
    target = '<a href="/x"><p>Hallo</p></a><p>Weiter {{name}}</p>'
    assert 'placeholder' in codes(validate_structure(source, target))


def test_deep_html_returns_structured_failure_instead_of_crashing():
    shallow = '<span>Hello</span>'
    assert validate_structure(shallow, shallow)['ok']
    deep = '<span>' * 1100 + 'Hello' + '</span>' * 1100
    result = validate_structure(deep, deep)
    assert not result['ok']
    assert result['errors']
    assert {'code', 'path', 'message'} <= result['errors'][0].keys()


def test_cli_batch_keeps_results_when_a_document_exceeds_recursion_depth():
    script = Path(__file__).resolve().parents[1] / 'validator' / 'structure.py'
    deep = '<span>' * 1100 + 'Hello' + '</span>' * 1100
    request = {'pairs': [
        {'id': 'deep', 'source': deep, 'target': deep},
        {'id': 'good', 'source': '<p>Hello</p>', 'target': '<p>Hallo</p>'},
    ]}
    completed = subprocess.run([sys.executable, str(script)], input=json.dumps(request),
                               text=True, capture_output=True, check=False)
    assert not completed.stderr
    assert completed.returncode == 1
    response = json.loads(completed.stdout)
    assert [(item['id'], item['ok']) for item in response['results']] == [('deep', False), ('good', True)]


def test_cli_excessively_nested_json_returns_input_error():
    script = Path(__file__).resolve().parents[1] / 'validator' / 'structure.py'
    completed = subprocess.run([sys.executable, str(script)], input='[' * 1100 + '0' + ']' * 1100,
                               text=True, capture_output=True, check=False)
    assert not completed.stderr
    assert completed.returncode == 1
    assert 'input' in codes(json.loads(completed.stdout))


@pytest.mark.parametrize('space,empty', [
    ('<span> </span>', '<span></span>'),
    ('<span><em> </em></span>', '<span><em></em></span>'),
    ('<span>\n </span>', '<span></span>'),
])
def test_preserve_text_keeps_significant_whitespace_inside_inline_elements(space, empty):
    source = '<p>Hello' + space + 'world</p>'
    assert validate_structure(source, source, preserve_text=True)['ok']
    assert 'text' in codes(validate_structure(source, '<p>Hello' + empty + 'world</p>', preserve_text=True))


@pytest.mark.parametrize('token,split', [
    ('{{name}}', '{{<em>name</em>}}'),
    ('{name}', '{<em>name</em>}'),
    ('${name}', '${<em>name</em>}'),
    ('%s', '%<em>s</em>'),
    ('%1$s', '%1$<em>s</em>'),
])
def test_placeholders_must_stay_intact_within_one_text_node(token, split):
    source = '<p>Hello ' + token + '<em>friend</em></p>'
    target = '<p>Hallo ' + split + 'Freund</p>'
    assert 'placeholder' in codes(validate_structure(source, target))
    assert 'placeholder' in codes(validate_structure(target, source))
    intact = '<p>Hallo <em>' + token + '</em>Freund</p>'
    assert validate_structure(source, intact)['ok']


def test_comment_cannot_split_a_placeholder():
    source = '<p>Hello {{name}}</p>'
    target = '<p>Hallo {{na<!-- comment -->me}}</p>'
    assert 'placeholder' in codes(validate_structure(source, target))
    assert validate_structure(source, '<p>Hallo <!-- comment -->{{name}}</p>')['ok']


def test_printf_argument_order_can_follow_translation_grammar():
    source = '<p>%s has %d files</p>'
    assert validate_structure(source, '<p>%d Dateien hat %s</p>')['ok']
    assert not validate_structure(source, '<p>%d Dateien hat %d</p>')['ok']
    assert not validate_structure(source, '<p>%d Dateien</p>')['ok']
