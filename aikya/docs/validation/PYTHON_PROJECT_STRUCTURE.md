# Python Project Structure Validation

This report preserves the initial local structure checkpoint, based on 08db487,
before publication. Version remains 6.1.1. The cleanup and package structure were
subsequently published through e3ca08d on feat/sdd-spec-coding-templates.

**Current follow-up:** the former 658-line SDD engine has been split into focused
modules; engine.py is now 282 lines and the largest implementation module is
404 lines. See [the separate modularization report](SDD_MODULARIZATION.md) for
current validation. The original measurements below remain historical evidence;
resource-path follow-up is recorded in [command acceptance](COMMAND_ACCEPTANCE.md).
No release tag or package publication was created.

## Implemented structure

- Python implementations live under src/aikya/, grouped into core, tools, middleware, memory, installation, discovery, workflows, documentation, catalogs, routing and quality. Existing root scripts remain compatibility adapters, using one bootstrap at the compatibility boundary.
- The bounded SDK runtime, file permissions, settings approval and loop are reused. Memory extraction consumes the same permission functions; no duplicate model client, Bash tool layer, context compressor or vector store was added.
- The installer has explicit source/template context, a compatible facade and focused profile, discovery, interview, checks, IO, migration, asset, preflight, configuration, document and pipeline modules. Its old 344-line coordinator is split into bounded stages.
- The shared runtime inventory handles registration and initialized projects, canonical source resources, stable installed destinations, ODD/SDD entry-point selection and gallery omission. Package code selection excludes unrelated data; actual .env files are excluded while public .env.example templates remain eligible.
- 296 source resource files moved once into resources/. Pinned Milkeles bytes and licenses remain unchanged. The two first-party instruction assets were deliberately updated for the canonical record policy; the migration receipt preserves both original and destination hashes.
- The 981-line migration hash literal became a checksummed JSON resource and small loader. All original mapping entries, including five retired-command records, remain unchanged. Separately captured predecessor hashes allow reviewed pre-package upgrades without trusting an ownership marker alone.
- Coupled package customization blocks upgrade before launchers change. Managed replacements retain backups, detect stale previews and restore previous file bytes after the tested copy failure; retries succeed. Existing decoupled custom legacy adapters and project-owned documents remain preserved.
- Usage aggregation sits below CLI orchestration, and command metadata is independent of registration. Existing deferred document-composition compatibility calls remain; cold import acceptance verifies that supported module orders work.
- pyproject.toml defines the package, Python floor, VERSION metadata, console scripts and optional SDK extra. Ordinary runtime dependencies remain empty. Build tooling was installed only into a temporary environment.
- Contributor instructions, English/Spanish README structure, CI source/resource paths and package acceptance were updated. CI builds the distributions and tests a wheel outside the checkout, without the optional SDK.

## Canonical records

All new Aikya plans use aikya/docs/plan/, bugs use aikya/docs/bugs/, and features
use aikya/docs/features/. SDD plan.md remains in its authoritative specification
dossier under aikya/docs/specs/; it is not duplicated under plan/.

The writer normalizes legacy plural plan inputs. CI validates changed Markdown
before the no-source-change shortcut; Stop snapshots detect newly misplaced
records even without code changes. Symlinked/unsafe candidates are rejected before
reading content. Unmarked project-owned documentation is preserved. Installed
reference assets are recognized through matching ownership-manifest hashes rather
than being mistaken for new living reports. Existing host instructions, project
entry README files, technical analysis reports and protected template assets retain
their functional locations. Private memory remains outside Git.

## Observed full regression matrix

| Python | Tests | Result | Seconds |
|---|---:|---|---:|
| 3.10 | 490 | OK | 265.608 |
| 3.11 | 490 | OK | 253.133 |
| 3.12 | 490 | OK | 295.39 |
| 3.13 | 490 | OK | 283.817 |

- All four full runs passed. The provider scanner now closes its bounded Terraform read; its regression first reproduced the former ResourceWarning, then passed. No ResourceWarning appears in the final matrix logs.
- The 48 onboarding combinations passed in every suite: three types × two methods × two locales × two registration scopes × init/analyze. CLIs run from an unrelated cwd with PYTHONPATH empty and actual canonical document assertions.
- All 14 example profiles passed offline smoke checks. Metadata is valid for 30 agents, 29 technical skills and 27 public commands. All 120 Milkeles templates and 155 reference files passed integrity validation.
- Eight wheel onboarding cases passed in a fresh virtual environment, without the SDK and without source-checkout imports. Installed document guards and optional-runtime-unavailable checks also passed.
- 91 installed modules passed cold imports in two independent process orders, including reverse order. Every imported implementation came from the isolated environment.
- Actual upgrades from the Git baseline passed for both registration scopes and both ODD/SDD initialized projects. A custom locale adapter was preserved, installed guards remained usable and repeated upgrades succeeded.
- New transaction tests cover a controlled adapter copy failure and restoration of previously copied package bytes, successful retry, and owner edits after preview. Additional tests cover customized coupled code, symlinks, gallery backup conflicts and secret-file exclusion.
- Private scope, tool permissions, loop recovery/adversarial behavior, SDD approvals, ODD continuity, footer/index contracts and historical migrations remain covered by the full suite. Authenticated provider acceptance is still a separate, user-assigned environment activity.

## Sizes and artifacts

At the initial checkpoint, the package contained 92 Python files; the largest was 658 lines. install.py is a 16-line adapter and installation/facade.py is 191 lines. All 28 former installer callable parameter signatures remain present. The registered inventory contains 513 files and 2,605,973 raw source bytes, with the 265-file historical gallery excluded. The retained source gallery remains checksummed.

Full source quality inspected 239 files: zero size/syntax errors, 12 review warnings, including 3 repeated-body groups. Existing long functions and historical fixture similarities remain review diagnostics; the former install.py file-size failure is resolved. This is a maintainability check, not a security certification.

- aikya_harness-6.1.1.tar.gz: 823417 bytes; SHA-256 f2ef906d054a8e1c67ff59ce666e9033f2b8d9e77259a9531a089c22c3eaf82a.
- aikya_harness-6.1.1-py3-none-any.whl: 1135543 bytes; SHA-256 1e06760a85c6d0800919313994295a75db0619458261365cf5737471e86005f9.


Both wheel and sdist contain the required host settings template, reference
catalog and license. They omit bytecode caches, actual .env files, historical
gallery outputs, live repository records and repository test fixtures. The
project-template harness test is an intentional distributable asset. Artifacts
were built locally from the sdist path, inspected and not published.

## Evidence and reproduction

- Run python3.X -m unittest discover -s tests -p 'test_*.py' -v for X = 10, 11, 12, 13.
- Run python3 scripts/ci/smoke_profiles.py, scripts/ci/check_assets.py and scripts/ci/validate_agent_assets.py.
- Run python3 documentation_templates.py check and python3 code_quality.py --all.
- Run python3 scripts/ci/context_budget.py --max-proxy-tokens 6000; observed proxy: 3,356. This is not billed usage.
- In an explicitly prepared build environment, run python -m build --no-isolation, then python scripts/ci/package_smoke.py --wheel dist/aikya_harness-6.1.1-py3-none-any.whl.
- The baseline-upgrade probe used git archive 08db487 in temporary directories, ran the baseline installer/registrar there, then upgraded through the current source and exercised the installed commands. It made no remote calls.

See [machine-readable results](PYTHON_PROJECT_STRUCTURE_RESULTS.json),
[module mapping](PYTHON_MODULE_MIGRATION.json), [resource move receipt](PYTHON_RESOURCE_MIGRATION.json),
[implementation plan](../plan/2026-10-23-python-project-structure.md),
[feature acceptance](../features/python-package-structure/spec.md) and
[discovery bug record](../bugs/bugs.md).

GENERATED BY AIKYA HARNESS
