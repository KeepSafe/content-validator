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
| Task 1: pyproject, Python 3.11, dependency audit | Applicable | Replace legacy packaging with `pyproject.toml`, set Python 3.11 policy, bump version to `1.0.0`, hard-pin runtime deps, upgrade Python 3.11-incompatible deps, and modernize source syntax. |
| Task 2a: formatting and Flake8 alignment | Applicable | Keep 120-char style in `pyproject.toml`, use `flake8-pyproject`, and fix lint only as needed. |
| Task 2b: hooks, CI, Makefile, README | Partial | Normalize Makefile, README, existing Travis workflow, and add CircleCI for this package. Service runner targets are not required for this no-stack repo. |
| Task 2c: mypy stabilization | Not applicable | No existing typing contract or service baseline requires mypy for this small library in this migration. |
| Task 3: msgpack/redis/asynctest/nose | Partial | Replace `nose` with `pynose`. No `msgpack` dependency exists in `pyproject.toml`, and no redis, aioredis, or asynctest usage exists. |
| Task 4: asyncio/aiohttp modernization | Applicable | Upgrade `aiohttp`, keep URL checker request behavior, and remove Python 3.11-incompatible loop usage in tests. |
| Task 4c: async test harness modernization | Applicable | Keep the lightweight local helper but remove removed `loop=` APIs and validate async URL tests. |
| Task 5: Gunicorn/Docker local infra | Not applicable | No service runtime or local backing services. |
| Task 6: requirements build pipeline | Partial | Keep simple package requirements files aligned with `pyproject.toml`; no ansible service lockfile pipeline applies. |

## Skill Guardrail Audit

- Preflight: `python3.11`, `rg`, and `gh` were present. Docker/service daemon checks were not run because the repo audit
  classified this as no-stack library/tool shape.
- Branching: used the requested single `python311-upgrade` branch for this no-stack repo instead of six stacked service
  PRs. The branch split is documented here.
- Service contract tooling: the bundled service contract verifier and CI gate require service-template assertions. They
  are not applicable to this package because there is no Paste/Gunicorn/INI/healthcheck service surface to validate.
- `libks==1.0.0`: not applicable; `content-validator` does not depend on `libks`.
- `LIBKS_VERSION` Makefile extraction: not applicable for the same reason.
- CircleCI sample addition: applicable by team request. The branch adapts the skill sample
  `resources/python-services/samples/circleci_config.yml` into a native CircleCI 2.1 `.circleci/config.yml`. Reusable
  `executors` and `commands` replace the sample's YAML-anchor layout, with schema-correct restore and save cache
  commands. The config retains `prepare_cache`, `lint`, and `test` jobs, `cimg/python:3.11.13`, versioned `v4-pip-`
  / `v4-venv-` fallback cache keys, xUnit/coverage XML artifact storage, and the sample non-fatal Codecov upload step.
  The install job uses this repo's `make ci-dev-install` target and loads the same KeepSafe organization SSH key
  fingerprint as `email-service` before dependency installation. The current `KeepSafe/html-structure-diff` dependency
  is public and installs from an HTTPS tag, but the key keeps CI ready for private organization dependencies. The
  matching key must be provisioned in this CircleCI project's SSH-key settings.
- `PYNOSE_SHARED_FLAGS`: applicable. Makefile test flow uses the sample-style coverage-inclusive pynose flags and adds
  CI XML/xunit artifact flags under `ifdef CI`.
- Runtime `print()` guardrail: `ConsoleReporter` intentionally prints user-facing report output for a library reporter,
  not long-running service runtime output.

## Dependency Audit Notes

Upgraded because Python 3.11 compatibility or modern tooling required it:

- `aiohttp >=3,<3.4` / `aiohttp==3.1.3` -> `aiohttp==3.13.2`: old versions fail to import on Python 3.11 due removed
  `asyncio.coroutines._DEBUG`; `3.13.2` is the team-required target and its exercised request behavior passes locally.
- `beautifulsoup4 >=4,<5` / `beautifulsoup4==4.4.1` -> `beautifulsoup4==4.15.0`: selected as the current Python
  3.11-compatible package set and covered by existing HTML/URL fixture tests.
- `lxml >=3` / `lxml==3.5` -> `lxml==6.1.1`: old pin lacks the target Python 3.11 wheel/runtime baseline; parser and
  reporter fixtures cover the exercised behavior.
- `Markdown` / unpinned -> `Markdown==3.10.2`: pinned to the resolved Python 3.11-compatible runtime set and covered by
  markdown diff fixtures.
- `parse <= 1.8.2` / `parse==1.8.2` -> `parse==1.22.1`: latest available version passed parser, URL, and fixture
  coverage locally.
- `sdiff @ git+https://github.com/KeepSafe/html-structure-diff.git@0.4.1` ->
  `sdiff @ git+https://github.com/KeepSafe/html-structure-diff.git@1.0.0`: latest tagged version installed, imported,
  and passed existing HTML/markdown structure-diff fixture coverage locally.
- `flake8==3.6.0` -> `flake8==7.3.0` plus `flake8-pyproject==1.2.4`: old flake8 fails with modern setuptools because
  `pkg_resources` is no longer available by default.
- `nose` -> `pynose==1.5.5`: old nose fails on Python 3.11 due removed `collections.Callable`.

Dependency target refresh on 2026-07-21:

- Team-required target: `aiohttp==3.13.2` (intentionally retained instead of a newer release).
- Refreshed pins: `beautifulsoup4==4.15.0`, `lxml==6.1.1`, `parse==1.22.1`, and `coverage==7.15.2`.
- Other validated pins: `Markdown==3.10.2`, `build==1.5.0`, `flake8==7.3.0`, `flake8-pyproject==1.2.4`,
  `pynose==1.5.5`, `twine==6.2.0`, `setuptools>=82.0.1`, and `wheel>=0.47.0`.
- Current/latest git tag: `sdiff @ git+https://github.com/KeepSafe/html-structure-diff.git@1.0.0`.
- Msgpack: not applicable. `msgpack` is not a `content-validator` dependency and there are no direct source/test
  msgpack call sites to migrate.

## Proof Commands

Default proof must be local/free and must not call production, paid providers, or public external service APIs.

- `python3.11 -m venv venv`
- `venv/bin/pip install -e '.[dev]'`
- `make lint`
- `make test`
- `make ci-dev-install`
- `CI=1 make test`
- `circleci config validate .circleci/config.yml`
- `circleci config process .circleci/config.yml`
- `venv/bin/python -m compileall validator tests`
- Import smoke for `validator`, `validator.checks.url`, `aiohttp`, `bs4`, `lxml`, `markdown`, `parse`, and `sdiff`.
- Golden compatibility tests over existing fixtures, with URL network calls mocked.
- CLI smoke: `venv/bin/content-validator --help`.
- `venv/bin/pip check`

## Known Gaps

- Dependency version discovery and installation require package index/GitHub access, but behavior proof must not call
  production or paid provider APIs.

## Migration Results

Date: 2026-05-11, skill audit refreshed 2026-05-13 and dependency targets refreshed 2026-07-21.

Branch: `python311-upgrade`

Completed applicable work:

- Replaced `setup.py` / `setup.cfg` with `pyproject.toml`.
- Set Python policy to `3.11.13` in `.python-version` and `>=3.11,<3.12` in package metadata.
- Bumped package version from `0.7.2` to `1.0.0`.
- Hard-pinned runtime dependencies in `pyproject.toml` and aligned `requirements.txt`.
- Upgraded Python 3.11-incompatible dependencies:
  - `aiohttp >=3,<3.4` / `aiohttp==3.1.3` to the team-required `aiohttp==3.13.2`; old import failed on removed
    `asyncio.coroutines._DEBUG`.
  - `beautifulsoup4` to `4.15.0`, `lxml` to `6.1.1`, `Markdown` to `3.10.2`, `parse` to `1.22.1`, and `sdiff` to
    tag `1.0.0` as the latest Python 3.11 package set.
  - `flake8==3.6.0` to `flake8==7.3.0` plus `flake8-pyproject==1.2.4`; old flake8 failed on removed
    `pkg_resources`.
  - `nose` to `pynose==1.5.5`; old nose failed on removed `collections.Callable`.
- Added fixture-backed golden compatibility tests for markdown diff shape, Java placeholders, and URL extraction.
- Added a minimal `content-validator` CLI help/version smoke surface because package metadata already declared the
  console script.
- Updated README, Travis command, native CircleCI 2.1 config, Makefile, and git hook target for the Python 3.11
  package workflow.
- Refreshed the Makefile test flow to use sample-style `PYNOSE_SHARED_FLAGS`, including coverage-inclusive defaults and
  CI XML/xunit artifact flags under `ifdef CI`.
- Added sample-style CI cache/install targets: `ci-env` reuses a valid cached venv or recreates it, and
  `ci-dev-install` installs `requirements-dev.txt` from public sources before installing the package editable without
  re-resolving dependencies. Local development and publishing retain the private-index-aware `PIP_ARGS` where needed.
- Added explicit dependency audit notes and latest-version proof for runtime, build, and test pins.

Proof results:

- `python3.11 --version`: Python 3.11.13.
- `make clean`: pass.
- `make dev`: pass with package-index/GitHub dependency resolution.
- `make ci-dev-install`: pass with public package-index/GitHub dependency resolution and no internal `pypicloud` probe.
- `make test`: pass, 65 tests, 1 skipped, coverage total 84%.
- `CI=1 make test`: pass, 65 tests, 1 skipped, writes `build/coverage/coverage.xml` and `build/test/results.xml`.
- `venv/bin/flake8 --version`: reports `7.3.0` with `Flake8-pyproject: 1.2.4`.
- `venv/bin/pynose --version`: reports `1.5.5`.
- `venv/bin/python -m compileall validator tests`: pass.
- Import smoke for `validator`, `validator.checks.url`, `aiohttp==3.13.2`, `beautifulsoup4==4.15.0`,
  `lxml==6.1.1`, `Markdown==3.10.2`, `parse==1.22.1`, and `sdiff==1.0.0`: pass.
- `venv/bin/content-validator --help` and `venv/bin/content-validator --version`: pass.
- `venv/bin/pip check`: pass.
- `venv/bin/python -m build .`: pass; built local sdist and wheel under ignored `dist/`.
- `circleci config validate .circleci/config.yml`: pass; CircleCI CLI reported the version 2.1 config is valid.
- `circleci config process .circleci/config.yml`: pass with CircleCI API access; reusable executors and commands expand
  into the expected `prepare_cache`, `lint`, and `test` jobs.
- `make hooks`: pass after escalation to write shared git metadata; hook was removed afterward with `make unhooks`.

Service-only tasks intentionally skipped:

- No Gunicorn, PasteDeploy, service INI, health endpoint, worker, Docker local infra, or ansible service requirements
  pipeline was added.

Known gaps after migration:

- Dependency installation/build proof required network access to package indexes and GitHub for the tagged `sdiff`
  dependency.
- Downstream repos still need their own requirements recompilation against `content-validator==1.0.0`.
