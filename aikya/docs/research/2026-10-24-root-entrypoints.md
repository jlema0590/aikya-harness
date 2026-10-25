# Root Python entry points: verified structure analysis

Date: 2026-10-24. Version: 7.0.0. Analysis branch:
`refactor/root-entrypoints-cleanup`, created directly from the refreshed
`origin/develop` commit `d37f090918fe0ec6d97787170b784108759bd70a`.
That commit merges PR #18 and contains the package restructuring.

## Finding

The application implementation has already moved into `src/aikya/`. Root files
such as `aikya_session.py` are compatibility entry points retained during that
migration. They are not a second implementation of their target module.

There are 53 Python files directly at the repository root:

- 51 compatibility adapters, each 16 physical lines, with no top-level function
  or class definitions. Every declared canonical module resolves to an existing
  implementation under `src/aikya/`.
- `_aikya_bootstrap.py`: a 39-line compatibility loader that activates the adjacent
  source package and passes entry-file context for runtime/project resolution.
- `setup.py`: a 34-line setuptools build hook that stages distribution resources
  and validates the optional SDK dependency declaration. It is build tooling.

The complete mapping and counts are recorded in
[the inventory](2026-10-24-root-entrypoints-inventory.json).

| Root entry point | Actual implementation | Purpose |
|---|---|---|
| `aikya_session.py` | `src/aikya/cli/session.py` | SessionStart greeting and onboarding guidance |
| `aikya_cli.py` | `src/aikya/cli/main.py` | Main local CLI |
| `aikya_setup.py` | `src/aikya/installation/registration.py` | Global/project registration |
| `install.py` | `src/aikya/installation/facade.py` | Installer compatibility facade |
| `agent_loop.py` | `src/aikya/core/loop.py` | Bounded optional execution loop |
| `documentation_templates.py` | `src/aikya/documentation/templates.py` | Offline catalog and reviewed documentation |

## Why aikya_session.py remains at the root

The root adapter calls `aikya.cli.session`. When imported normally, it aliases
the canonical package module rather than copying its functions into a separate
implementation. The identity check `aikya_session is aikya.cli.session` returned
True; its implementation file is `src/aikya/cli/session.py` (71 physical lines).

The retained location supports these current contracts:

1. **Existing startup hooks.** Registration generates commands targeting the
   installed runtime's `aikya_session.py`: a shared user runtime for global scope
   and `.aikya/runtime/aikya_session.py` for project scope. See
   `src/aikya/installation/registration.py`, lines 313–318.
2. **Hook recognition.** Registration prevents duplicate startup hooks by checking
   for that filename, and the installer recognizes a managed bootstrap settings
   file the same way. These checks are at registration lines 148–150 and
   `src/aikya/installation/facade.py`, lines 75–83.
3. **Runtime distribution.** `installation/assets.py` derives its adapter inventory
   from `module_map.json` and requires those source files to exist. Deleting a
   required root adapter currently makes runtime preparation fail.
4. **Package construction.** The `setup.py` build hook copies root adapters into
   the wheel's distribution resources. `MANIFEST.in` also includes root Python
   files in the source distribution. A naive deletion can omit required adapters
   from a wheel, while source-runtime preparation rejects a missing file.
5. **Source consumers and tests.** Existing imports and source instructions use
   names such as `import aikya_session`, `import install` and `aikya_setup.py`.
   They remain part of the compatibility surface even though the package uses
   canonical imports internally.

The adapter also enables source-tree execution without requiring an editable
package installation, including execution from an unrelated current directory.
Moving it into `src/` without revising the loader and consumers is not equivalent
because it changes the script path and package-discovery boundary.

## Assessment and recommended direction

The package migration moved the implementation successfully. Root cleanup was
intentionally deferred to retain existing interfaces, and the remaining 51 small
adapters make the repository look less consolidated than the actual codebase.
This is compatibility debt and repetitive launcher code, not 51 unused business
modules. The root location is not a permanent requirement of the session logic.

For a subsequent approved cleanup, retain canonical implementation modules and
centralize adapter generation from `module_map.json` for installed runtimes.
This can preserve installed legacy filenames without maintaining 51 launcher
files at the source root. Build staging, runtime inventory/source resolution,
ownership receipts and upgrade protections must use that generated asset source.

Migrate source CLI callers, tests and documentation to the existing package and
console entry points (`aikya`, `aikya-setup`, or explicit Python modules in a
configured package environment). Those two console commands already exist in
`pyproject.toml`; session inspection currently uses its Python module, not a
separately declared session console command.

Preserving installed runtime paths does **not** preserve removed source-root
commands such as `python3 aikya_session.py` or uninstalled legacy imports. Their
retirement must be documented, or a small, explicitly chosen compatibility
surface must remain. Keep ordinary packaging configuration at the root;
`setup.py` should be evaluated as build infrastructure, separately from launchers.

Verify fresh global/project registration, both methodologies, repeated upgrades,
custom settings and assets, startup/status hooks, unrelated-directory execution,
installed wheel behavior and package metadata before removing any adapter.
The old installed paths need migration only if the cleanup elects to change them.

## Verification performed

- Root inventory: 53 Python files, 51 verified adapters, 56 module-map entries
  including five helpers supplied through project-template assets.
- Static inspection: all root adapter targets exist, and each adapter lacks
  top-level function/class implementations.
- Direct import identity check for the session adapter: passed.
- `python3 -B -m unittest discover -s tests -p test_package_contracts.py -v`:
  5 tests passed, covering shared legacy/package identity, unrelated-directory
  package execution, dry runs, private-file filtering and customized runtime safety.
- `python3 -B -m unittest discover -s tests -p test_v56.py -v`:
  10 tests passed, including the global SessionStart greeting, project layout,
  controlled generator fixtures, custom-file protection and managed hook migration.

This task creates the local analysis branch and documentation. It does not move
or remove runtime code, change the version, or claim that adapter removal has
been implemented. All new analysis artifacts are under `aikya/docs/`.

GENERATED BY AIKYA HARNESS
