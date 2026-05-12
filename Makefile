PYTHON=venv/bin/python
PIP=venv/bin/pip
NOSE=venv/bin/pynose
FLAKE=venv/bin/flake8
PYPICLOUD_HOST=pypicloud.getkeepsafe.local
PIP_ARGS=--extra-index-url http://$(PYPICLOUD_HOST)/simple/ --trusted-host $(PYPICLOUD_HOST)
TWINE=./venv/bin/twine
FLAGS=

build-dir:
	mkdir -p build/test build/coverage

env:
	test -d venv || python3.11 -m venv venv
	$(PIP) install -U pip setuptools wheel
	$(PIP) install $(PIP_ARGS) -e .

dev: env
	$(PIP) install $(PIP_ARGS) -e '.[dev]'

install: env

publish: dev
	rm -rf dist
	$(PYTHON) -m build .
	$(TWINE) upload --verbose --sign --username developer --repository-url http://$(PYPICLOUD_HOST)/simple/ dist/*.whl

flake:
	$(FLAKE) validator tests

check-msgpack:
	@true

lint: build-dir flake check-msgpack

test-only: build-dir
	$(NOSE) -s $(FLAGS)

test: lint test-only

vtest vtests: build-dir
	$(NOSE) -s -v $(FLAGS)

cov cover coverage: build-dir
	$(NOSE) -s --with-coverage --cover-inclusive --cover-erase --cover-package=validator \
		--cover-html --cover-html-dir ./coverage $(FLAGS)
	echo "open file://`pwd`/coverage/index.html"

ci-env: clean env

ci-dev-install: dev

hooks:
	cp git_hooks/pre-push `git rev-parse --git-path hooks/pre-push`
	chmod +x `git rev-parse --git-path hooks/pre-push`

unhooks:
	rm -f `git rev-parse --git-path hooks/pre-push`

clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -f `find . -type f -name '@*' `
	rm -f `find . -type f -name '#*#' `
	rm -f `find . -type f -name '*.orig' `
	rm -f `find . -type f -name '*.rej' `
	rm -f .coverage
	rm -rf coverage
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	rm -rf venv


.PHONY: build-dir env dev install publish flake check-msgpack lint test-only test vtest vtests cov cover coverage ci-env \
	ci-dev-install hooks unhooks clean
