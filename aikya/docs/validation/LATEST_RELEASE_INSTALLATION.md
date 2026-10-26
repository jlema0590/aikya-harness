# Latest Release Installation Validation

Date: 2026-10-25. Target version: **7.0.1**. Baseline commit: `371360edb09c619a2457e995e28bbed8f13950c0`.

## Delivered behavior

- The English and Spanish quick starts download platform scripts from permanent `releases/latest/download` URLs; users no longer enter a release number.
- Online `install` and `update` default to GitHub's latest published stable release. `--version latest` has the same behavior. The resolver rejects drafts, prereleases, malformed JSON, missing publication metadata and nonnumeric tags.
- Resolve the version once, then fetch the wheel and checksum manifest through that version's immutable download URLs. Existing SHA-256 checks, wheel metadata checks, explicit scopes and installation recovery remain active.
- Preserve optional numeric version selection through `--version X.Y.Z` and PowerShell `-Version X.Y.Z`. Numeric pins do not query the latest-release API.
- Each platform script verifies its own version-pinned bootstrap before executing it. Even a reused script selects the latest harness online. Offline, the script supplies its embedded release version; direct manager/bootstrap calls require an explicit numeric version.
- Prepare `VERSION` and the collected release notes as **v7.0.1**. This work does not publish release assets or change existing release tags.

## Observed checks

| Check | Observed result |
|---|---|
| Full regression, Python 3.11.11 | **534 passed**, 690.813 seconds, exit code 0 |
| New latest-selection and executable-script regression tests | 8 passed on macOS with Python 3.10, 3.12 and 3.13; 8 passed on Debian with Python 3.13 |
| Installer-focused suite, including existing rejection/recovery cases | 33 passed on macOS Python 3.13 |
| Release workflow/version tests | 16 passed |
| Wheel and source distribution build | `aikya_harness-7.0.1-py3-none-any.whl` and `aikya_harness-7.0.1.tar.gz` built successfully |
| Isolated wheel onboarding without source imports | 8/8 passed: global/project × ODD/SDD × init/analyze; no agent SDK installed |
| Default latest selection through real provisioning | Global/project install, update, doctor and uninstall passed using the real 7.0.1 wheel and controlled HTTPS responses; four independent version resolutions, 12 reads, matching receipts/checksums and preserved user document |
| macOS ARM64 clean installer, Python 3.13.2 | Global/project installation, update, managed startup, new ODD/en initialization, existing SDD/es analysis and uninstall passed |
| Debian ARM64 clean installer, Python 3.13.17 | Same lifecycle passed without network or elevated privileges, with a read-only repository |
| Alpine ARM64 clean installer, Python 3.12.15 | Same lifecycle passed without network or elevated privileges, with a read-only repository |
| Catalog and example profiles | 30 agents, 29 skills, 27 commands consistent; 14/14 profiles passed |
| Changed source quality | 5 inspected source files; no errors, warnings or duplicate bodies |
| Whole source quality scan | No errors; existing long-function warnings and three implementation/legacy-fixture duplicate pairs remain outside this change |
| Documentation layout and exact index | Passed after final report/index refresh; all authored documents have one terminal footer |
| Live read-only GitHub lookup | The real resolver returned **6.1.1**, GitHub's selected latest stable release at validation time; no published release was installed |

The full regression completed successfully. Negative-path tests also emit expected failure/rejection messages; these are distinct from unittest failures.

The installer-focused suite emits an expected negative-check message (`INVALID_CWD` / `RESULTADO: FAILED`) while testing rejection of an unsafe working directory; unittest itself completed with `OK` and exit code 0.

Full regression log SHA-256: `bfd6b0658dd8fbd9d88358f6f1b1b8f652bd3e9821af8d5b4651695e0db91f86`.

## Test environment finding

The first Debian run of the new script tests failed because Docker mounted the disposable temporary directory with `noexec`. The real installation lifecycle passed in that environment. The test's temporary Python/download executables could not start. `/proc/mounts` confirmed the cause; rerunning only the regression test container with execution enabled in its temporary directory passed all eight tests. No production-code workaround was added.

## Publication and platform limits

The latest-release lookup follows [GitHub's documented latest full release endpoint](https://docs.github.com/en/rest/releases/releases#get-the-latest-release), and the README uses its [latest release asset links](https://docs.github.com/en/repositories/releasing-projects-on-github/linking-to-releases).

The current latest published release predates these installer assets. The README explicitly states that the entry script URLs become usable when **v7.0.1** is published. Publication remains gated by the repository's release workflow.

Native Windows/PowerShell execution was not performed locally. The native installer workflow runs the new tests on Windows, Linux and macOS with Python 3.10–3.13; its remote results must be observed separately. No authenticated model session was run.

GENERATED BY AIKYA HARNESS
