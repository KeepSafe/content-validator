"""Actionable diagnostics through the public API and standalone JSON CLI."""
import json
from pathlib import Path
import subprocess
import sys

from validator.structure import validate_structure


def test_nested_protected_attributes_show_expected_and_found_values():
    result = validate_structure('<div><p id="start" class="b a">Hello</p></div>',
                                '<div><p id="end" disabled>Hallo</p></div>')
    error = next(error for error in result['errors'] if error['code'] == 'attribute')
    assert error['path'] == '/div[1]/p[1]'
    assert 'expected {"class": ["a", "b"], "id": "start"}' in error['message']
    assert 'found {"disabled": null, "id": "end"}' in error['message']
    assert set(error) == {'code', 'path', 'message'}


def test_placeholder_diagnostics_include_identity_count_and_attribute_boundary():
    source = '<p>{{name}} {{name}} <img src="/x" alt="Photo {count}"></p>'
    target = '<p>{{name}} {{user}} <img src="/x" alt="Foto {total}"></p>'
    errors = validate_structure(source, target)['errors']
    prose = next(error for error in errors if error['path'] == '/p[1]')
    assert 'expected {"{{name}}": 2}' in prose['message']
    assert 'found {"{{name}}": 1, "{{user}}": 1}' in prose['message']
    attribute = next(error for error in errors if error['path'] == '/p[1]/img[1]')
    assert 'alt placeholder' in attribute['message']
    assert 'expected {"{count}": 1}' in attribute['message']
    assert 'found {"{total}": 1}' in attribute['message']


def test_block_diagnostics_include_counts_and_order():
    error = validate_structure('<div><h2>Title</h2><p>Body</p></div>',
                               '<div><p>Text</p></div>')['errors'][0]
    assert error['code'] == 'structure'
    assert error['path'] == '/div[1]'
    assert 'expected 2 ["h2", "p"]; found 1 ["p"]' in error['message']


def test_cli_inline_diagnostics_identify_changed_link_nesting_and_duplicate_count():
    script = Path(__file__).resolve().parents[1] / 'validator' / 'structure.py'
    request = {'pairs': [
        {'id': 'accepted', 'source': '<p><a href="/x">Help</a><em>Now</em></p>',
         'target': '<p><em>Jetzt</em><a href="/x">Hilfe</a></p>'},
        {'id': 'link', 'source': '<p><a href="/help">Help</a></p>',
         'target': '<p><a href="/other">Hilfe</a></p>'},
        {'id': 'nested', 'source': '<p><strong><em>Hello</em></strong></p>',
         'target': '<p><strong>Hallo</strong></p>'},
        {'id': 'duplicate', 'source': '<p><em>Hello</em></p>',
         'target': '<p><em>Hallo</em><em>Welt</em><em>Jetzt</em></p>'},
        {'id': 'run', 'source': '<div><p>Body</p><a href="/x">Help</a></div>',
         'target': '<div><p>Text</p><a href="/y">Hilfe</a></div>'},
    ]}
    completed = subprocess.run([sys.executable, str(script)], input=json.dumps(request),
                               text=True, capture_output=True, check=False)
    assert completed.returncode == 1
    assert completed.stderr == ''
    response = json.loads(completed.stdout)
    assert set(response) == {'ok', 'results'}
    assert response['results'][0] == {'id': 'accepted', 'ok': True, 'errors': []}
    for result in response['results'][1:]:
        assert result['ok'] is False
        assert set(result) == {'id', 'ok', 'errors'}
        assert all(set(error) == {'code', 'path', 'message'} for error in result['errors'])
    link, nested, duplicate, run = [item['errors'][0] for item in response['results'][1:]]
    assert link['path'] == '/p[1]'
    assert '"href": "/help"' in link['message']
    assert '"href": "/other"' in link['message']
    assert 'missing' in link['message'] and 'unexpected' in link['message']
    assert '"tag": "em"' in nested['message'] and '"children"' in nested['message']
    assert '"count": 2' in duplicate['message']
    assert 'inline run 2' in run['message']


def test_exact_mode_and_attribute_presence_remain_distinguishable():
    exact = validate_structure('<img src="/x" alt="Photo">',
                               '<img src="/x" alt="Bild">', preserve_text=True)
    error = next(error for error in exact['errors'] if error['code'] == 'attribute')
    assert 'exact-content mode' in error['message']
    assert '"alt": "Photo"' in error['message'] and '"alt": "Bild"' in error['message']
    presence = validate_structure('<img src="/x" alt>', '<img src="/x">')
    assert 'alt presence differs: expected present; found absent' in presence['errors'][0]['message']


def test_code_and_platform_label_diagnostics_identify_expected_and_found_content():
    code = validate_structure('<pre><code>print(1)\n</code></pre>',
                              '<pre><code>print(2)\n</code></pre>')
    error = next(error for error in code['errors'] if error['code'] == 'code')
    assert 'expected "print(1)\\n"; found "print(2)\\n"' in error['message']
    tabs = validate_structure('<h2 class="tab-label">iOS</h2>',
                              '<h2 class="tab-label">iPhone</h2>')
    error = next(error for error in tabs['errors'] if error['code'] == 'platform_label')
    assert 'expected "iOS"; found "iPhone"' in error['message']
