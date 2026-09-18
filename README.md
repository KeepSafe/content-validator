content-validator [![Build Status](https://travis-ci.org/KeepSafe/content-validator.svg?branch=master)](https://travis-ci.org/KeepSafe/content-validator)
=================

Content validator looks at text content and preforms different validation tasks.

## Requirements

1. Python 3.6.6+

## Installation

`make install`

## Dev Setup

`make env`
`make dev`

## Usage

Generally it's easiest to write a separate test for each validation case. The simplest example:

```
f = files('src/**/*.txt')
parser = create_parser(Filetype.txt)
reporter = ConsoleReporter()
check = urls(Filetype.txt)
result = validator.validate(checks=[check], files=f, parser=parser, reporter=reporter)
self.assertEqual([], result)
```

### Files

The `files` function takes a pattern and resolves it to file paths. You can pass any glob like pattern but in addition you can include the parameters. The parameter is used when you want to compare content. Let's say you have translations in English and German. You have two files `src/en/myfile.txt`  and `src/de/myfile.txt` for English and German. The pattern might look something like this `src/{lang}/myfile.txt`. In addition you need to say which file will be the base of the comparison, in case you have more then 2 files. To do that you need to pass all parameters you are using in the pattern as named parameters for the `files` call. Finally the call should look something like this:

`files('src/{lang}/*.txt', lang='en')`

In case you are not doing any comparison checks you can use a usual glob like pattern `files('src/**/*.txt')`

### Parsers

When the file is first read it the data you want to validate needs to be extracted from it. The simplest example is a text file. Nothing is done here except reading the file content. The more complex example is when, for eg., you have embedded markdown in an xml tag. To extract the data you should create a chain of parsers. First you want to extract all tags from the xml. Second you want to parse the content of the tags from markdown to html. Here is an example how to do that:

`chain_parsers([Filetype.xml, Filetype.md], query='//strings')`

The xml parser takes additional parameter `query` used to extract the tags. You can pass it to `create_parser` in the same way:

`create_parser(Filetype.xml, query='//strings')`

Available parsers types:

* `Filetype.txt` - simply reads the file
* `Filetype.md` - converts markdown to
* `Filetype.xml` - extracts text from xml and concatenates
* `Filetype.csv` - puts every value on a separate line

### Reporters

Shows the result of the validation. There are 2 reporters available:

* `HtmlReporter` - creates an error file for every error
* `ConsoleReporter` - print the error to the console

### Checks

Checks perform validation on the content. Wether it's url or structure or anything else. If the content in not valid the check will return an error which later can be passed to a reporter.

Available checks:

* `urls(filetype, skip_images=False)` - validates if the url is accessible
* `markdown()` - validates markdown structure by comparing it with the base

## Example

A more detailed example looks like this:

```
class TestEmail(TestCase):

    def test_email(self):
        f = files('src/{lang}/*.xml', lang='en')
        parser = create_parser(Filetype.xml, query='.//string')
        reporter = HtmlReporter()
        md = markdown()
        result = validator.validate(checks=[md], files=f, parser=parser, reporter=reporter)
        self.assertEqual({}, v.validate())

    def test_urls(self):
        f = files('src/{lang}/*.xml', lang='en')
        parser = chain_parsers([Filetype.xml, Filetype.md], query='.//string')
        reporter = ConsoleReporter()
        check = urls(Filetype.html, skip_images=True)
        result = Validator(checks=[check], files=f, parser=parser, reporter=reporter)
        self.assertEqual({}, v.validate())
```

## Rich Markdown and HTML translation structure

`validator.structure.validate_structure` adds an opt-in structural contract for translated HTML and Markdown. It preserves block order/nesting, immutable attributes and link destinations, code, placeholder counts, and tab identity, while permitting translated prose, accessible text, and grammatical inline reordering. It returns `{ "ok": true, "errors": [] }` or structured errors with `code`, `path`, and `message`.

```python
from validator.structure import validate_structure

result = validate_structure(
    '<p>Hello {{name}}. <a href="/help">Help</a></p>',
    '<p>Hallo {{name}}. <a href="/help">Hilfe</a></p>',
)
```

For ordinary Markdown, pass `source_format='markdown'` and/or `target_format='markdown'`. The default uses Python Markdown. For custom syntax, supply `markdown_renderer=your_renderer`, or render both documents with the application's authoritative renderer and validate the resulting HTML. Unrendered `:::` directives are rejected: they must not silently pass as plain prose. The help-center app uses the HTML adapter so tabs, steps, callouts, and raw fragments are validated with exactly the renderer used by the website.

The standalone CLI works with Python 3.11+ and only the standard library for HTML inputs; the Markdown option additionally requires the `Markdown` package. From a pinned checkout, run:

```sh
python3 validator/structure.py < comparison.json
```

Input is `{ "source": "...", "target": "...", "source_format": "html", "target_format": "html" }`, or `{ "pairs": [{ "id": "article/locale", "source": "...", "target": "..." }] }` for batch validation. Output is JSON; exit 0 means accepted and exit 1 means validation failed or the request was invalid. Optional `preserve_text: true` also compares text and attribute values for migration parity instead of permitting translation.

This validator expects explicitly closed HTML fragments and rejects common malformed nesting instead of silently applying browser repairs. It is not a sanitizer, a complete HTML5 conformance validator, or proof of translation meaning. Placeholder support is an explicit subset (brace and printf forms), not a full ICU-message parser. Existing Markdown/URL checks retain their previous behavior; callers opt into this new contract.

Inline code may reorder with the grammar of a translated paragraph while its exact content stays protected. Inline elements cannot cross block boundaries, including blocks inside link wrappers. Placeholders in accessible attributes are preserved per attribute, separately from prose.

See the [translation structure code review guide](docs/translation-structure-review.md) for the contract, accepted and rejected examples, and review checks.

Targeted verification: `python -m pytest tests/test_structure.py`.
