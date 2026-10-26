# Generated Runtime Adapters and Clean Installer Validation

Baseline: `d37f090918fe0ec6d97787170b784108759bd70a` (develop). Branch: `refactor/root-entrypoints-cleanup`. Package version remains `7.0.0`; changes are documented under Unreleased. No tag or release was published.

## Implementation

- Remove 51 source-root compatibility launchers and the root bootstrap. Only `setup.py` remains as root Python build infrastructure; implementations stay under `src/aikya/`.
- Generate all 56 compatibility entry points from one mapping and launcher template. Frozen adapter hashes, installed destinations, fresh helper context and module alias behavior remain tested. The five helper launchers are generated outputs instead of maintained source-template copies.
- Share file/generated asset reads, provenance digests and runtime transactions. Detect generator/mapping/template drift after preview, reject symlinks before reading templates, preserve custom coupled assets and retain recoverable backups.
- Build wheel/sdist from canonical resources without root-launcher staging. Repository tests and CI use canonical imports, including dynamic imports and command dispatch.
- Deliver one stdlib installer core as package modules and a deterministic standalone zipapp. Render version-pinned Linux/macOS and PowerShell scripts with bootstrap SHA-256 verification; install the release wheel into final-path per-user environments without Git, SDK dependencies or activation.
- Serialize installation changes, record ownership, preserve edited files and keep interpreters referenced by initialized projects. Receipts store generated settings deltas and hashes instead of unrelated user credentials.
- Use the selected Python for managed hooks and known Aikya quality checks, preserve the stored SDD gate contract, and quote PowerShell/statusline commands separately. Public slash commands and ODD/SDD choices remain unchanged.

## Observed regression results

| Python | Tests | Result |
| --- | --- | --- |
| 3.10 | 523 | passed |
| 3.11 | 526 | passed |
| 3.12 | 523 | passed |
| 3.13 | 523 | passed |

Full regression acceptance: **passed**. Each complete suite includes both 48-case onboarding matrices and the existing 78 SDD lifecycle fingerprints. Subtests are not added to the unittest count. Following the completed suites, focused current-code groups were also run on every Python version: 5 generated-asset safety tests, 4 managed-hook tests and 5 installer-core tests. These overlap the full suites and are reported separately, not summed as distinct full-suite tests.

| Verification | Observed result |
| --- | --- |
| Public commands, macOS | 27 commands; 49 executable support checks passed |
| Public commands, Linux | 27 commands; 49 executable support checks passed from the installed wheel, with network disabled |
| Profiles and instruction assets | 14 profiles; 30 agents; 29 skills; 27 slash commands valid |
| Offline documentation catalog | 120 pinned templates |
| Wheel acceptance | 8 global/project × ODD/SDD × init/analyze cases passed |
| Wheel rebuilt from sdist | Rebuilt without root adapters; the same 8 cases passed |
| v7 baseline upgrades | Both scopes passed repeated upgrade; custom settings preserved; edited coupled code blocked before launcher changes |
| Source quality | No errors, warnings or duplicate bodies reported |

## Real installer platform checks

The same candidate wheel, bootstrap and script assets passed on macOS ARM64 and Debian, Alpine and Fedora ARM64. Linux test containers ran as an unprivileged user with a read-only root, a temporary writable directory and **network disabled**. Prerequisites were supplied by the test images, outside the end-user installer.

Each platform exercised the entry script, both registration scopes, repeated installation/update, startup-hook execution, new-project ODD initialization in English, existing-project SDD analysis in Spanish, documentation guards and uninstall. User documents/settings survived; initialized projects still passed their guard after registration removal because their referenced interpreter remained available.

## Failures found and corrected

1. Fedora exposes virtual environments through `lib64`. Canonicalizing package resource roots fixes the mismatch between resolved registration paths and resource lookup; a symlink-library regression test and the real Fedora rerun pass.
2. Removing root files exposed remaining dynamic test imports, source-script invocations and source-helper assumptions. Consumers now load canonical modules or explicitly generated installed fixtures; the source-consumer guard checks dynamic imports too.
3. Changing the stored SDD gate interpreter broke exact gate recognition. Preserve its stored contract and resolve only the exact known Aikya check commands through the current interpreter at execution time; custom commands remain untouched.
4. A symlinked launcher template was compiled before input safety validation. Reject it before reading/compiling, covered by a failing-then-passing regression test.
5. Application launchers initially had scope-specific ownership. A single application ownership manifest now allows global/project coexistence without treating the other scope's launchers as custom files.
6. Persisting full settings snapshots could duplicate credentials, and generic settings detection included a runtime template. Persist only generated changes for the exact user/project settings path; removal preserves unrelated additions and rejects edited owned hooks before runtime deletion.

7. A locally edited installed generator template must block a coupled upgrade; the new 5-test generated-asset group proves that protection on Python 3.10–3.13.
8. Translating project hooks must preserve explicit timeouts and leave an unspecified timeout unspecified; the hook group verifies both cases.
9. Empty platform storage variables must fall back to per-user storage instead of selecting the working directory; the installer-core group verifies the Linux fallback, and the Windows fallback follows the same rule.

## Remaining environment and publication gates

- Native Windows has a prepared PowerShell installer and a 12-job native OS/Python CI matrix, plus Linux distribution jobs. Windows was **not executed** on this macOS host; no Windows-native or authenticated-client success is claimed.
- Actual Claude Code sessions/model execution remain for the separate environment selected by the user. Command-support tests execute real Python/subprocess behavior without claiming model-driven slash-command coverage.
- A future authorized release must publish these new assets under its own version. Existing v7.0.0 release assets are not rewritten. Publication is gated on the native/distro installer jobs and immutable release-asset verification.
- Compatible Python 3.10–3.13 with venv/pip is required; Python itself is not bundled or silently installed. Legacy runtimes lacking a clean-installer receipt require explicit adoption review; their existing registration upgrade path was tested separately.
- Recovery covers handled file operations. An interrupted pending operation is reported for review; no whole-project or power-failure atomicity is claimed.

Detailed observed receipts and artifact hashes: [validation JSON](GENERATED_RUNTIME_ADAPTERS.results.json). Source plan: [implementation plan](../plan/2026-10-24-generated-runtime-adapters.md).

GENERATED BY AIKYA HARNESS
