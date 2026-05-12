# content-validator Python 3.11 Migration Contract

## Scope

`content-validator` is a no-stack library/tool migration. The repo exposes a Python package named `validator` and a
`content-validator` console entry point, but it has no PasteDeploy app factory, Gunicorn config, service INI files,
health endpoint, worker process, or local service dependencies. Service-only `python311-service-upgrade-stack` tasks are
therefore intentionally not part of this migration unless a later audit proves new service shape.

Edit root: `/Users/olmos/keepsafe/repos/worktrees/content-validator-python-upgrade`
Branch plan: single reviewable branch, `python311-upgrade`, created from `master`.
First write scope: this contract, packaging/test workflow, and golden compatibility tests.

## Public Surfaces

- Python API: `validator.parse()` builder chain and `validator.checks` helpers for markdown, URL, URL occurrence, and
  Java argument validation.
- Importable modules used downstream: `validator`, `validator.errors`, `validator.checks.url`.
- CLI surface: `content-validator` console script declared by package metadata.
- Behavior-sensitive fixtures: existing markdown, URL occurrence, parser bug, flat text, Java placeholder, and report
  fixtures under `tests/fixtures/`.

## Downstream Consumers

Local scan found these active consumers:

- `email-service`: depends on `content-validator` through `setup.py` / requirements and imports `validator` in
  `mailman/cms/validation.py`.
- `translation-real-time-validaton`: pins `content-validator == 0.7.2`, imports `validator`, and directly imports
  `validator.checks.url.DEFAULT_USER_AGENT`, `TextUrlExtractor`, `UrlStatusChecker`, and `UrlDiff`.
- `ansible`: installs `content-validator` for the `zendesk-knowledgebase-editor` role.

Downstream unblocked criteria: package installs on Python 3.11, imports the documented modules, preserves fixture-backed
validation behavior, and publishes dependency pins that downstream requirement compilers can resolve.

## Baseline Audit

- Packaging: legacy `setup.py` / `setup.cfg`, version `0.7.2`, `.python-version` is `3.6.8`.
- Runtime dependencies: `aiohttp >=3, <3.4`, `Markdown`, `parse <= 1.8.2`, `beautifulsoup4 >=4, <5`, `lxml >=3`,
  and direct tagged dependency `sdiff @ git+https://github.com/KeepSafe/html-structure-diff.git@0.4.1`.
- Dev/test dependencies: `nose`, `flake8==3.6.0`, `coverage`, `twine`, `build`.
- Test runner: Makefile uses `nosetests`; Travis calls non-existent `make tests`.
- Service audit: no service shape found.
- Python 3.11 baseline result before migration:
  - `make test` failed because `flake8==3.6.0` imports removed `pkg_resources` with current setuptools.
  - `venv/bin/nosetests -s` failed because `nose` references removed `collections.Callable`.
  - `import aiohttp` failed because `aiohttp<3.4` references removed `asyncio.coroutines._DEBUG`.

## Task Mapping

| Skill task | Applicability | Plan |
| --- | --- | --- |
| Task 1: pyproject, Python 3.11, dependency audit, pyupgrade | Applicable | Replace legacy packaging with `pyproject.toml`, set Python 3.11 policy, bump version to `1.0.0`, hard-pin runtime deps, upgrade Python 3.11-incompatible deps, and run pyupgrade. |
| Task 2a: formatting and Flake8 alignment | Applicable | Keep 120-char style in `pyproject.toml`, use `flake8-pyproject`, and fix lint only as needed. |
| Task 2b: hooks, CI, Makefile, README | Partial | Normalize Makefile, README, and existing Travis workflow for this package. Service runner targets and CircleCI additions are not required for this no-stack repo. |
| Task 2c: mypy stabilization | Not applicable | No existing typing contract or service baseline requires mypy for this small library in this migration. |
| Task 3: msgpack/redis/asynctest/nose | Partial | Replace `nose` with `pynose`. No msgpack, redis, aioredis, or asynctest usage exists. |
| Task 4: asyncio/aiohttp modernization | Applicable | Upgrade `aiohttp`, keep URL checker request behavior, and remove Python 3.11-incompatible loop usage in tests. |
| Task 4c: async test harness modernization | Applicable | Keep the lightweight local helper but remove removed `loop=` APIs and validate async URL tests. |
| Task 5: Gunicorn/Docker local infra | Not applicable | No service runtime or local backing services. |
| Task 6: requirements build pipeline | Partial | Keep simple package requirements files aligned with `pyproject.toml`; no ansible service lockfile pipeline applies. |

## Proof Commands

Default proof must be local/free and must not call production, paid providers, or public external service APIs.

- `python3.11 -m venv venv`
- `venv/bin/pip install -e '.[dev]'`
- `make lint`
- `make test`
- `venv/bin/python -m compileall validator tests`
- Import smoke for `validator`, `validator.checks.url`, `aiohttp`, `bs4`, `lxml`, `markdown`, `parse`, and `sdiff`.
- Golden compatibility tests over existing fixtures, with URL network calls mocked.
- CLI smoke: `venv/bin/content-validator --help`.
- `venv/bin/pip check`

## Known Gaps

- Local interpreter is `python3.11.9`; the shared service skill defaults `.python-version` to `3.11.13`. This repo will
  declare `3.11.13`, while local verification records the available `3.11.9` runtime unless `3.11.13` is installed.
- Dependency version discovery and installation require package index/GitHub access, but behavior proof must not call
  production or paid provider APIs.

## Migration Results

Date: 2026-05-11

Branch: `python311-upgrade`

Completed applicable work:

- Replaced `setup.py` / `setup.cfg` with `pyproject.toml`.
- Set Python policy to `3.11.13` in `.python-version` and `>=3.11,<3.12` in package metadata.
- Bumped package version from `0.7.2` to `1.0.0`.
- Hard-pinned runtime dependencies in `pyproject.toml` and aligned `requirements.txt`.
- Upgraded Python 3.11-incompatible dependencies:
  - `aiohttp >=3,<3.4` / `aiohttp==3.1.3` to `aiohttp==3.13.5`; old import failed on removed
    `asyncio.coroutines._DEBUG`.
  - `beautifulsoup4` to `4.14.3`, `lxml` to `6.1.0`, and `Markdown` to `3.10.2` as the resolved Python 3.11
    package set.
  - `flake8==3.6.0` to `flake8==7.3.0` plus `flake8-pyproject==1.2.4`; old flake8 failed on removed
    `pkg_resources`.
  - `nose` to `pynose==1.5.5`; old nose failed on removed `collections.Callable`.
- Kept `parse==1.8.2` and tagged `sdiff` dependency to avoid unnecessary behavior drift.
- Ran pyupgrade ladder through `--py311-plus`.
- Added fixture-backed golden compatibility tests for markdown diff shape, Java placeholders, and URL extraction.
- Added a minimal `content-validator` CLI help/version smoke surface because package metadata already declared the
  console script.
- Updated README, Travis command, Makefile, and git hook target for the Python 3.11 package workflow.

Proof results:

- `make clean`: pass.
- `make dev`: pass with package-index/GitHub dependency resolution.
- `make test`: pass, 65 tests, 1 skipped.
- `venv/bin/python -m compileall validator tests`: pass.
- Import smoke for `validator`, `validator.checks.url`, `aiohttp==3.13.5`, `beautifulsoup4==4.14.3`,
  `lxml==6.1.0`, `Markdown==3.10.2`, `parse==1.8.2`, and `sdiff`: pass.
- `venv/bin/content-validator --help` and `venv/bin/content-validator --version`: pass.
- `venv/bin/pip check`: pass.
- `venv/bin/python -m build .`: pass; built local sdist and wheel under ignored `dist/`.
- `make hooks`: pass after escalation to write shared git metadata; hook was removed afterward with `make unhooks`.

Service-only tasks intentionally skipped:

- No Gunicorn, PasteDeploy, service INI, health endpoint, worker, Docker local infra, or ansible service requirements
  pipeline was added.

Known gaps after migration:

- Verification ran with local `python3.11.9`; `.python-version` declares the shared target `3.11.13`.
- Dependency installation/build proof required network access to package indexes and GitHub for the tagged `sdiff`
  dependency.
- Downstream repos still need their own requirements recompilation against `content-validator==1.0.0`.
