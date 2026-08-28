PYTHON=venv/bin/python
PIP=venv/bin/pip
NOSE=venv/bin/pynose
FLAKE=venv/bin/flake8
PYPICLOUD_HOST=pypicloud.getkeepsafe.local
PIP_ARGS=--extra-index-url http://$(PYPICLOUD_HOST)/simple/ --trusted-host $(PYPICLOUD_HOST)
TWINE=./venv/bin/twine
SDIFF_VERSION=$(shell sed -n 's/^[[:space:]]*"sdiff==\([^"[:space:]]*\)"[[:space:]]*,[[:space:]]*$$/\1/p' pyproject.toml)
SDIFF_CI_SOURCE=sdiff @ git+https://github.com/KeepSafe/html-structure-diff.git@$(SDIFF_VERSION)
PYNOSE_SHARED_FLAGS=-s --with-coverage --cover-inclusive --cover-erase --cover-package=validator tests
PYNOSE_FLAGS=$(PYNOSE_SHARED_FLAGS)
ifdef CI
PYNOSE_FLAGS += --cover-xml --cover-xml-file=build/coverage/coverage.xml --with-xunit --xunit-file=build/test/results.xml
endif
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
	$(NOSE) $(PYNOSE_FLAGS) $(FLAGS)

test: lint test-only

vtest vtests: build-dir
	$(NOSE) -v $(PYNOSE_FLAGS) $(FLAGS)

cov cover coverage: build-dir
	$(NOSE) $(PYNOSE_FLAGS) --cover-html --cover-html-dir ./coverage $(FLAGS)
	echo "open file://`pwd`/coverage/index.html"

ci-env:
	@if [ -d "venv" ] && $(PIP) --version >/dev/null 2>&1; then \
		echo "Reusing cached CI venv"; \
	else \
		echo "No cached venv found, creating fresh venv..."; \
		rm -rf venv; \
		python3.11 -m venv venv; \
	fi
	$(PIP) install -U pip setuptools wheel

ci-dev-install: ci-env
	$(PIP) install "$(SDIFF_CI_SOURCE)"
	$(PIP) install -e ".[dev]"

check-sdiff-requirements:
	./utils/update_sdiff_requirements.sh --check

update-sdiff-requirements:
	./utils/update_sdiff_requirements.sh

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
	ci-dev-install check-sdiff-requirements update-sdiff-requirements hooks unhooks clean
