# Unified Harness and Mods installation — v7.1.0

Date: 2026-10-26. Branch: `feat/unified-installation-mods`.

## Implemented behavior

- Clean installation defaults to global Harness + Flow + Usage; BoxBot/all,
  individual plugins and Harness-only installation remain explicit selections.
- Harness and Mods resolve independent published stable versions once. The bundle
  is checksum verified, safely extracted and retained as a versioned local source;
  upstream installers are never executed. No Mods implementation is vendored.
- Native Claude JSON operations preserve external plugins and track intent before
  mutation, per-scope ownership, successful checkpoints and partial failures.
  Updates retain registered IDs; legacy Harness-only receipts do not gain plugins.
- Shared pure policy drives standalone management and embedded entry previews.
  Dry-run performs no downloads, writes or Claude commands. Managed user PATH
  entries are reversible; Windows changes notify applications without changing
  execution policy or system PATH.
- Unified management and Pages entries require Harness 7.1.0+. Older wheels do not
  carry the new management contract. Pages publishes exact verified release script
  bytes and provenance, via a workflow invoked after successful release publication.
- Flow remains session-connected through `/aikya-flow connect <cache-root>`;
  installing it does not imply a persistent automatic evidence connection.

## Observed verification

| Check | Observed result |
|---|---|
| Complete regression run with frozen sources and loopback permission, before the final UTF-8 transport refinement | 624 tests, 2 skipped, no failures/errors; 919.636 seconds |
| Final installer regression subset | 53 tests passed, including real native Claude management and PowerShell 7 |
| Memory regression after native CI review | 48 tests passed; numeric loopback startup succeeds with hostname resolution unavailable |
| Final user PATH tests | 5 passed, including registry preservation and environment broadcast |
| Final Pages tests | 2 passed: exact release bytes, integrity blocking and legacy rejection |
| Verified Mods distributions | 7 passed: persistent source ownership, SHA-256, malformed catalogs, ZIP traversal/links/duplicates/expansion, Unicode collisions and forged disk markers |
| Public command acceptance | 28 commands, 52 executable checks passed |
| Catalog and example profiles | 30 agents, 29 skills, 28 commands; 14/14 profiles passed |
| Isolated wheel acceptance | 8 global/project × ODD/SDD × init/analyze cases passed, including local memory HTML and document placement; optional SDK absent |
| Final v7.1.0 installer with published Mods v0.0.10 and real Claude 2.1.308, macOS | 6 global/project × recommended/all/none cases passed: install, update, doctor and uninstall |
| Native PowerShell entry with real Claude, macOS | PowerShell 7.6.9: project/all install and uninstall passed with Unicode/apostrophe paths |
| PowerShell caller scope | `iex` preview returned control and preserved caller preferences |
| Linux installer | Debian-based Python 3.13 and Alpine Python 3.12 containers passed global/project installation, update, initialization and conservative removal |
| Git prohibition probe | Real native marketplace/plugin install and removal completed with a failing Git guard; Git was not invoked |
| New Mods packaging format | Locally built unpublished v0.0.14 fixture verified successfully; not treated as a published release |

The 624-test run used code revision `565aba0`. The following UTF-8 refinement was
verified by 53 installer tests, including four regressions observed failing first:
native JSON decoding, managed Python output, component-receipt decoding and
non-Latin CLI diagnostics under a simulated CP1252 locale. Results are separated
by snapshot rather than attributed to one run.

Native macOS CI at `05ccb86` exposed a separate live-view startup failure:
`test_live_client_reuses_session_observer_and_releases_only_its_lease` did not
receive the ready URL within 30 seconds on Python 3.10 and 3.13. The HTTP server's
default bind calls `socket.getfqdn` even for numeric loopback; the first server
test took approximately 35 seconds. A regression with hostname lookup blocked
failed before the fix and passed after bypassing that lookup for the explicit
loopback server. All 48 memory tests then passed locally in 27.861 seconds.
The PR checks below record the resulting native rerun rather than treating the
earlier readiness timeout as successful acceptance.

The native installer matrix at `565aba0` also passed all 12 OS/Python combinations
and the three Linux distribution jobs. The current revision's full and native
results are recorded in [PR #22 checks](https://github.com/jlema0590/aikya-harness/pull/22/checks);
that live record is authoritative for the PR head.

Reproducible checks:

```sh
python -B -m unittest discover -s tests -p 'test_*.py' -q
python -B scripts/ci/command_acceptance.py --output /tmp/aikya-commands.json
python -B scripts/ci/check_assets.py
python -B scripts/ci/smoke_profiles.py
python -B scripts/ci/package_smoke.py --wheel <assets>/aikya_harness-7.1.0-py3-none-any.whl
python -B scripts/ci/installer_smoke.py --assets <assets>
python -B scripts/ci/mods_installer_smoke.py --assets <harness-assets> --mods-assets <mods-assets>
```

The last check requires a native Claude CLI and uses disposable homes/configuration.
GitHub CI runs the native entry, bundle, selection, PATH and Pages tests across
Windows/macOS/Linux and Python 3.10–3.13. A native Claude installation test is skipped
where that executable is absent; this is separate from fixture/protocol acceptance.

## Earlier failed run and resolution

An initial sandboxed run completed 614 tests with one failure, four errors and two
skips. The following results were superseded by the frozen-source, loopback-enabled
subsequent frozen-source runs above; no memory-runtime product change was needed:

- `test_engineering_catalog.EngineeringCatalogTests.test_project_setup_includes_catalog_and_global_does_not_mutate_projects`:
  the runtime correctly rejected a source file edited during package preflight.
- `test_memory_live.MemoryLiveTests.test_authorized_snapshot_uses_latest_complete_publication`,
  `test_memory_live.MemoryLiveTests.test_custom_html_or_torn_report_is_not_served_as_current`,
  `test_memory_live.MemoryLiveTests.test_no_arbitrary_paths_foreign_host_origin_or_missing_capability`:
  sandbox permissions denied the test-owned loopback server bind.
- `test_memory_integration.MemoryIntegrationTests.test_live_client_reuses_session_observer_and_releases_only_its_lease`:
  the live client could not stay running under the same loopback restriction.

New feature regressions were observed failing before implementation and then
passing, including recovery after interrupted registration/update/removal,
side-effect-free entry preview, version compatibility and Windows source aliases.

## Publication and acceptance limits

- No release or Pages site has been published by this work. The short URLs require
  the reviewed code to reach a published v7.1.0+ release and a successful Pages
  deployment; the workflow refuses drafts, prereleases and legacy installers.
- Native Windows PowerShell 5.1/registry acceptance is covered by the remote
  Windows installer jobs; the current head must retain those checks. PowerShell 7
  on macOS alone is not evidence of a Windows host run.
- No authenticated model execution, live host-pane rendering or automatic
  persistent Flow connection is claimed. Tests do not call AI models.
- Existing unrelated marketplace sources or shared sources that cannot safely be
  moved require review. Persistent source directories and plugin data are retained
  conservatively, including when managed Mods are kept after Harness removal.

Windows environment notification follows the documented
[WM_SETTINGCHANGE contract](https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-settingchange).

GENERATED BY AIKYA HARNESS
