content-validator [![Build Status](https://travis-ci.org/KeepSafe/content-validator.svg?branch=master)](https://travis-ci.org/KeepSafe/content-validator)
=================

Content validator looks at text content and preforms different validation tasks.

## Requirements

1. Python 3.11

## Installation

`make install`

## Dev Setup

`make env`
`make dev`

Common local commands:

* `make env` - create `venv` and install the package runtime dependencies.
* `make dev` - install runtime and development/test dependencies.
* `make lint` - run flake8 using `pyproject.toml` configuration.
* `make test` - run lint and the test suite.
* `make coverage` - run tests with coverage and write the HTML report to `coverage/`.
* `make clean` - remove local build, coverage, cache, and virtualenv artifacts.

## Usage

Generally it's easiest to write a separate test for each validation case. The simplest example:

```
import validator

result = validator.parse().files('src/**/*.txt').check().url().validate()
self.assertEqual([], result)
```

### Files

The `files` function takes a pattern and resolves it to file paths. You can pass any glob like pattern but in addition you can include the parameters. The parameter is used when you want to compare content. Let's say you have translations in English and German. You have two files `src/en/myfile.txt`  and `src/de/myfile.txt` for English and German. The pattern might look something like this `src/{lang}/myfile.txt`. In addition you need to say which file will be the base of the comparison, in case you have more then 2 files. To do that you need to pass all parameters you are using in the pattern as named parameters for the `files` call. Finally the call should look something like this:

`files('src/{lang}/*.txt', lang='en')`

In case you are not doing any comparison checks you can use a usual glob like pattern `files('src/**/*.txt')`

### Parsers

When the file is first read it the data you want to validate needs to be extracted from it. The simplest example is a text file. Nothing is done here except reading the file content. The more complex example is when, for eg., you have embedded markdown in an xml tag. To extract the data you should create a chain of parsers. First you want to extract all tags from the xml. Second you want to parse the content of the tags from markdown to html. Here is an example how to do that:

`validator.parse().files('src/{lang}/*.xml', lang='en').xml(query='.//string').md().check().md().validate()`

The xml parser takes additional parameter `query` used to extract the tags:

`validator.parse().files('src/{lang}/*.xml', lang='en').xml(query='.//string')`

Available parsers types:

* `files(...).check()` - simply reads the file
* `.md()` - converts markdown to HTML
* `.xml(query='*')` - extracts text from XML and concatenates matching elements
* `.csv()` - puts every value on a separate line

### Reporters

Shows the result of the validation. There are 2 reporters available:

* `HtmlReporter` - creates an error file for every error
* `ConsoleReporter` - prints the error to the console

### Checks

Checks perform validation on the content. Whether it's url or structure or anything else. If the content is not valid the
check will return an error which later can be passed to a reporter.

Available checks:

* `.url(skip_images=False)` - validates if the url is accessible
* `.md()` - validates markdown structure by comparing it with the base
* `.java()` - validates Java placeholder/reference compatibility

## CLI

The package exposes a `content-validator` command. The current CLI is intentionally minimal; use `content-validator --help`
or `content-validator --version` for smoke checks, and use the Python API for validations.

## Example

A more detailed example looks like this:

```
class TestEmail(TestCase):

    def test_email(self):
        result = validator \
            .parse() \
            .files('src/{lang}/*.xml', lang='en') \
            .xml(query='.//string') \
            .check() \
            .md() \
            .validate()
        self.assertEqual([], result)

    def test_urls(self):
        result = validator \
            .parse() \
            .files('src/{lang}/*.xml', lang='en') \
            .xml(query='.//string') \
            .md() \
            .check() \
            .url(skip_images=True) \
            .validate()
        self.assertEqual([], result)
```
