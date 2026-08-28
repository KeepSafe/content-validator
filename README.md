content-validator [![Build Status](https://travis-ci.org/KeepSafe/content-validator.svg?branch=master)](https://travis-ci.org/KeepSafe/content-validator) [![CircleCI](https://circleci.com/gh/KeepSafe/content-validator.svg?style=svg)](https://circleci.com/gh/KeepSafe/content-validator)
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

### Regenerating requirements and deployment wheels

`pyproject.toml` is the package dependency source of truth. The committed
`requirements/requirements.txt` is a pypicloud-only, hash-enforced deployment
artifact, not the local developer or CircleCI install source.

- Local developer installs use `make env` or `make dev` from `pyproject.toml`.
- CircleCI installs the permanent sdiff Git tag, then installs the `dev` extra
  from `pyproject.toml` without accessing internal pypicloud.

For an `sdiff` release that is already available on internal pypicloud, update its
exact pin in `pyproject.toml`, then run:

```shell
make update-sdiff-requirements
```

The helper exits without starting Docker when `requirements/requirements.txt`
already has the same pin. Otherwise, it performs a targeted, hash-preserving
`pip-compile` inside the Linux deployment builder and updates the lock. It
requires Docker, VPN access to pypicloud, and the local builder image. Build the
image once from the local ansible repo's `builder` directory with
`make focal-fossa-local` if it is missing.

To check pin parity without changing files, use:

```shell
make check-sdiff-requirements
```

The check target exits with status 1 when the pins differ.

Use the ansible builder when a release needs the complete x86_64 and aarch64
deployment wheel set. Set `CONTENT_VALIDATOR_PATH` to the checkout or worktree
that should receive the generated lock:

```shell
# 1. Build the local Python 3.11 builder images.
ANSIBLE_BUILDER_PATH=/absolute/path/to/ansible/builder
CONTENT_VALIDATOR_PATH=/absolute/path/to/content-validator
cd "$ANSIBLE_BUILDER_PATH"
make focal-fossa-local

# 2. Resolve requirements and build wheels for both architectures. Pass 1 uses
#    pypicloud with public PyPI as a fallback for artifacts not yet mirrored.
make focal-fossa-packages-local DIST_PATH=/tmp/packages SRC_PATH="$CONTENT_VALIDATOR_PATH"

# 3. Upload the generated wheels to internal pypicloud. Credentials are stored
#    in 1Password under the pypicloud developer account.
TWINE_PASSWORD=<password> make upload-wheels

# 4. Rebuild the package list on both pypicloud nodes.
# http://10.10.1.166:8080/#/admin -> "Rebuild package list"
# http://10.10.2.107:8080/#/admin -> "Rebuild package list"

# 5. Audit the uploaded wheel set.
bash audit_pypicloud.sh

# 6. Resolve again using pypicloud as the only index. The combined requirements
#    artifact contains hashes for both deployment architectures.
make focal-fossa-relock-local DIST_PATH=/tmp/packages SRC_PATH="$CONTENT_VALIDATOR_PATH"

# 7. Copy the pypicloud-only deployment lock back into the target checkout.
cp /tmp/packages/20.04/requirements.txt "$CONTENT_VALIDATOR_PATH/requirements/requirements.txt"
```

The builder writes wheels and architecture-specific requirements under
`/tmp/packages/20.04`, plus the pypicloud-only combined lock at
`/tmp/packages/20.04/requirements.txt`.

#### Release

1. Bump the content-validator version in `pyproject.toml`.
2. Run `make clean`, `make dev`, and `make test`.
3. Commit the release changes and merge them to `master`.
4. Create the version tag with `git tag <version>`.
5. Push the tag with `git push origin <version>`.
6. Run `make publish` using the pypicloud developer credentials from 1Password.
7. Rebuild the package list on both internal nodes:
   - `http://10.10.1.166:8080/#/admin`
   - `http://10.10.2.107:8080/#/admin`

`make publish` builds the source distribution and wheel, then uploads the wheel
to internal pypicloud. A changed package must use a new version because the index
will reject an artifact whose filename already exists.

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
