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
- Sdiff integration: `sdiff.MdParser`, `sdiff.ZendeskHelpMdParser`, `sdiff.diff()`'s three-tuple result,
  `sdiff.renderer.HtmlRenderer`, rendered diff strings, and each returned error's `.message`.
- Importable modules used downstream: `validator`, `validator.errors`, `validator.checks.url`.
- CLI surface: `content-validator` console script declared by package metadata.
- Behavior-sensitive fixtures: markdown, nested Zendesk tabs/steps/styled callouts, deterministic HTML reports, URL
  occurrence, parser bug, flat text, and Java placeholder fixtures under `tests/fixtures/`.

## Downstream Consumers

Local scan found these active consumers:

- `email-service`: declares the released `content-validator==1.0.0` package in `pyproject.toml` and imports
  `validator` in `mailman/cms/validation.py`.
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
  is a KeepSafe-owned internal dependency installed from an immutable HTTPS commit. The key keeps CI ready for private
  organization dependencies and must be provisioned in this CircleCI project's SSH-key settings.
- Travis runtime: applicable. Travis intentionally uses Ubuntu Jammy with Python `3.11.9`, the Python 3.11 patch
  release supported by the established KeepSafe Travis environment. Local development and CircleCI remain on
  `3.11.13`; all three environments stay within the package's `>=3.11,<3.12` policy.
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
- `lxml >=3` / `lxml==3.5` -> `lxml==6.0.2`: old pin lacks the target Python 3.11 wheel/runtime baseline. The selected
  pin matches the final email-service `libks==1.0.12` dependency graph, which also requires `lxml==6.0.2`;
  parser and reporter fixtures cover the exercised behavior.
- `Markdown` / unpinned -> `Markdown==3.10.2`: pinned to the resolved Python 3.11-compatible runtime set and covered by
  markdown diff fixtures.
- `parse <= 1.8.2` / `parse==1.8.2` -> `parse==1.22.1`: latest available version passed parser, URL, and fixture
  coverage locally.
- `sdiff @ git+https://github.com/KeepSafe/html-structure-diff.git@0.4.1` -> internal `sdiff==2.0.0`: consume the
  reviewed Mistune 3 compatibility line from html-structure-diff PR 14 without resolving the unrelated public PyPI
  project. The permanent `2.0.0` tag resolves to reviewed commit
  `3bb941e9f1b209b17abe3b674d453ae829359665`, and the internal package index now serves the corresponding wheel.
- `flake8==3.6.0` -> `flake8==7.3.0` plus `flake8-pyproject==1.2.4`: old flake8 fails with modern setuptools because
  `pkg_resources` is no longer available by default.
- `nose` -> `pynose==1.5.5`: old nose fails on Python 3.11 due removed `collections.Callable`.

Dependency target refresh on 2026-08-27:

- Team-required target: `aiohttp==3.13.2` (intentionally retained instead of a newer release).
- Refreshed pins: `beautifulsoup4==4.15.0`, `lxml==6.0.2`, `parse==1.22.1`, and `coverage==7.15.2`.
- Other validated pins: `Markdown==3.10.2`, `build==1.5.0`, `flake8==7.3.0`, `flake8-pyproject==1.2.4`,
  `pynose==1.5.5`, `twine==6.2.0`, `setuptools>=82.0.1`, and `wheel>=0.47.0`.
- Python 3.11 release dependency: internal `sdiff==2.0.0` with `mistune==3.3.4`. Rechecked on 2026-08-27: GitHub's
  annotated `2.0.0` tag resolves to commit `3bb941e9f1b209b17abe3b674d453ae829359665`, and pypicloud serves
  `sdiff-2.0.0-py3-none-any.whl` with SHA-256
  `dcf2dae503d92d31814a0de586454c024f5cedcae029f1c2d3f93540b361dadf`.
- Msgpack: not applicable. `msgpack` is not a `content-validator` dependency and there are no direct source/test
  msgpack call sites to migrate.

Sdiff compatibility evidence established before this downstream change:

- The predecessor and target dependency combinations produced identical results for 2,164 normalized
  content-validator wrapper operations, with signature
  `82d6bb502ef13151361a3bd980b8a4043170d4ad42e4095af47afd9ab3e00929`.
- The html-structure-diff Mistune 0.8.4-versus-3.3.4 oracle covered 1,091 cases with zero mismatches.
- Standard Markdown, forced differences, links, lists, malformed inputs, direction marks, Zendesk tabs/steps/callouts,
  `MdDiff`, `ContentData`, and HTML report output were included. The two historical list/thematic-break
  `AttributeError` cases remain unchanged rather than being silently broadened in this dependency update.

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
- Import/version smoke for `validator`, `validator.checks.url`, `aiohttp`, `bs4`, `lxml==6.0.2`, `markdown`, `parse`,
  `sdiff==2.0.0`, and `mistune==3.3.4`.
- Golden compatibility tests over existing fixtures, with URL network calls mocked.
- CLI smoke: `venv/bin/content-validator --help` and `venv/bin/content-validator --version`.
- `venv/bin/pip check`
- Isolated build, Twine checks, extracted-sdist tests, and clean built-wheel install/behavior proof.

## Known Gaps

- Dependency version discovery and installation require package index/GitHub access, but behavior proof must not call
  production or paid provider APIs.

## Migration Results

Date: 2026-05-11, skill audit refreshed 2026-05-13 and dependency targets refreshed 2026-08-27.

Branch: `python311-upgrade`

Completed applicable work:

- Replaced `setup.py` / `setup.cfg` with `pyproject.toml`.
- Set Python policy to `3.11.13` in `.python-version` and `>=3.11,<3.12` in package metadata.
- Bumped package version from `0.7.2` to `1.0.0`.
- Hard-pinned runtime dependencies in `pyproject.toml` and generated the pypicloud-only, hash-enforced
  `requirements/requirements.txt` deployment lock for both supported architectures.
- Upgraded Python 3.11-incompatible dependencies:
  - `aiohttp >=3,<3.4` / `aiohttp==3.1.3` to the team-required `aiohttp==3.13.2`; old import failed on removed
    `asyncio.coroutines._DEBUG`.
  - `beautifulsoup4` to `4.15.0`, `lxml` to `6.0.2`, `Markdown` to `3.10.2`, `parse` to `1.22.1`, and `sdiff` to
    internal package version `2.0.0` with `mistune==3.3.4`.
  - `flake8==3.6.0` to `flake8==7.3.0` plus `flake8-pyproject==1.2.4`; old flake8 failed on removed
    `pkg_resources`.
  - `nose` to `pynose==1.5.5`; old nose failed on removed `collections.Callable`.
- Added fixture-backed golden compatibility tests for markdown diff shape, Java placeholders, URL extraction, nested
  Zendesk tabs/steps/styled callouts, exact `MdDiff`/`ContentData`, and deterministic `HtmlReporter` output. Added
  `MANIFEST.in` so the source distribution contains the fixture tree needed to run these tests.
- Added a minimal `content-validator` CLI help/version smoke surface because package metadata already declared the
  console script.
- Updated README, Travis command/runtime (`dist: jammy`, Python `3.11.9`), native CircleCI 2.1 config, Makefile, and git
  hook target for the Python 3.11 package workflow. Local development and CircleCI intentionally use Python `3.11.13`.
- Refreshed the Makefile test flow to use sample-style `PYNOSE_SHARED_FLAGS`, including coverage-inclusive defaults and
  CI XML/xunit artifact flags under `ifdef CI`.
- Added sample-style CI cache/install targets: `ci-env` reuses a valid cached venv or recreates it, and
  `ci-dev-install` preinstalls the permanent sdiff Git tag derived from the exact project pin before installing the
  package's `dev` extra from `pyproject.toml`. CircleCI does not install the pypicloud-only deployment lock. Local
  development and publishing retain the private-index-aware `PIP_ARGS` where needed.
- Added `check-sdiff-requirements` and `update-sdiff-requirements` targets. The helper enforces exact pin parity and
  uses the Linux deployment builder for a targeted, hash-preserving pypicloud-only relock.
- Added explicit dependency audit notes and latest-version proof for runtime, build, and test pins.

Proof results:

- Sdiff 2.0.0 pre-release downstream proof on 2026-08-27:
  - `make dev` installed exact html-structure-diff commit `3bb941e9f1b209b17abe3b674d453ae829359665` as
    `sdiff==2.0.0` with `mistune==3.3.4`.
  - Focused golden proof passed equivalent and intentionally different nested Zendesk translations, exact
    `MdDiff`/`ContentData` values, deterministic report semantics and full-file hash, and installed-version checks.
  - Flake8 and `CI=1 make test` passed 69 tests with 1 expected skip and 84% line coverage.
  - Imports confirmed `content-validator==1.0.0`, `sdiff==2.0.0`, `mistune==3.3.4`, and `lxml==6.0.2`;
    `pip check`, compileall, CLI help, and CLI version passed.
  - Separate clean source exports passed both `make dev` and the CircleCI path `CI=1 make ci-dev-install`, followed
    by all 69 tests. Neither proof reused the worktree virtualenv.
  - Isolated build and Twine checks passed. The candidate wheel metadata preserved the immutable sdiff commit
    reference. The sdist contains the complete test/fixture tree and passes all 69 tests after extraction; the runtime
    wheel excludes tests and fixtures.
  - A no-cache install of the built wheel cloned the exact sdiff commit, confirmed the four target package versions and
    public sdiff imports, passed CLI help/version and `pip check`, and reproduced focused equivalent/different Zendesk
    behavior.
  - Both CircleCI validation modes and config processing passed locally. Commit `79ccb6c` is pushed to
    `origin/python311-upgrade`; live draft PR 39 checks were inspected on 2026-08-27 and its CircleCI `prepare_cache`,
    `lint`, and `test` checks all passed. The uncommitted Travis runtime follow-up has not run remotely.
- `python3.11 --version`: Python 3.11.13.
- Travis follow-up: Ruby YAML parsing confirmed `.travis.yml` selects Ubuntu Jammy/Python `3.11.9` and uses the same
  public-safe `make ci-dev-install` plus `make test` flow as CircleCI; `.python-version` and CircleCI remain on
  Python `3.11.13`.
- Published sdiff 2.0.0 follow-up proof on 2026-08-27:
  - The internal simple index exposes `sdiff-2.0.0-py3-none-any.whl`; an isolated no-dependency download fetched that
    exact artifact from pypicloud.
  - A clean `make dev` selected the index-distributed `sdiff==2.0.0` (`direct_url.json` absent) with
    `mistune==3.3.4`; `pip check`, lint, and all 69 tests passed with 1 expected skip and 84% coverage.
  - A clean CircleCI-path install preinstalled permanent sdiff tag `2.0.0`, which resolves to reviewed commit
    `3bb941e9f1b209b17abe3b674d453ae829359665`, then accepted the exact `sdiff==2.0.0` runtime requirement without
    querying the private index. `make test` and `pip check` passed.
  - The rebuilt content-validator wheel and sdist pass Twine checks. Wheel metadata contains the permanent
    `Requires-Dist: sdiff==2.0.0` requirement instead of a VCS URL.
  - The ansible two-pass builder flow produced `requirements/requirements.txt`, a pypicloud-only combined deployment
    lock with hashes for x86_64 and aarch64. It is byte-for-byte identical to the final builder output under
    `/tmp/packages/20.04/requirements.txt`.
  - Clean focal-fossa x86_64 and aarch64 builder containers installed the combined lock from pypicloud, passed
    `pip check`, and imported the expected `aiohttp==3.13.2`, `lxml==6.0.2`, and `sdiff==2.0.0` packages. The x86_64
    proof also confirmed the complete runtime version set, including `mistune==3.3.4`.
  - `make check-sdiff-requirements` passes. A disposable stale-pin check exits 1 without mutation, and a real
    `sdiff==1.0.0` to `sdiff==2.0.0` builder round trip regenerated the exact committed lock with preserved hashes.
  - A fresh public-index-only `make ci-dev-install` preinstalled the permanent sdiff Git tag, installed `.[dev]` from
    `pyproject.toml`, and passed lint, all 69 tests, version checks, and `pip check` without pypicloud access.
  - CircleCI config validation and processing pass with the `requirements/requirements.txt` cache key. Isolated wheel
    and sdist builds pass Twine checks; the sdist includes the deployment lock and fixtures but no removed
    `requirements-dev.txt`, and wheel metadata contains only the expected runtime and optional dev dependencies.
- Historical migration `make clean`: pass. It was intentionally not rerun for the earlier 2026-08-27 follow-up so the
  pre-existing untracked `.coverage` file remained present; fresh proof used isolated `/tmp` source exports instead.
- `make dev`: pass with the published internal sdiff wheel and public fallback for dependencies not yet mirrored.
- `make ci-dev-install`: pass with public package-index/GitHub dependency resolution and no internal `pypicloud` probe;
  CI preinstalls the matching permanent sdiff tag before checking the exact version requirement.
- `make test`: pass, 69 tests, 1 skipped, coverage total 84%.
- `CI=1 make test`: pass, 69 tests, 1 skipped, writes `build/coverage/coverage.xml` and `build/test/results.xml`.
- `venv/bin/flake8 --version`: reports `7.3.0` with `Flake8-pyproject: 1.2.4`.
- `venv/bin/pynose --version`: reports `1.5.5`.
- `venv/bin/python -m compileall validator tests`: pass.
- Import smoke for `validator`, `validator.checks.url`, `aiohttp==3.13.2`, `beautifulsoup4==4.15.0`,
  `lxml==6.0.2`, `Markdown==3.10.2`, `parse==1.22.1`, index-pinned `sdiff==2.0.0`, and
  `mistune==3.3.4`: pass.
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

Downstream status after migration:

- As of 2026-08-28, email-service PR #439 declares `content-validator==1.0.0`, consumes the published
  `sdiff==2.0.0` and `mistune==3.3.4` chain, and includes it in the combined x86_64/aarch64 hash lock.
- Its synchronized Python 3.11 environment passes `pip check`, and its local integration suite includes a real
  in-memory Markdown structure comparison through content-validator, sdiff, and Mistune.

## Email-service downstream correction

Date: 2026-08-04, updated 2026-08-28.

The final email-service resolver proof confirms that `libks==1.0.12` requires
`lxml==6.0.2`. The previous content-validator pin, `lxml==6.1.1`, made the two
packages impossible to resolve in one environment. The target is therefore
`lxml==6.0.2`, which remains Python 3.11-compatible and is covered by the same
parser, URL, report, and golden fixture tests. The same downstream audit
now has the released `content-validator==1.0.0` consuming the published internal `sdiff==2.0.0` requirement with
`mistune==3.3.4`. Email-service PR #439 now carries the regenerated combined requirements and downstream integration
proof against that permanent release dependency chain.
