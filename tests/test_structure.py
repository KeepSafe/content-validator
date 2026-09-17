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
