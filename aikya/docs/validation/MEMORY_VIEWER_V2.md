# Memory viewer version 2 acceptance

Date: 2026-10-26. Branch: `feat/automatic-local-memory`.

## Result and scope

The actual exporter now generates the approved Java preview's navy theme and
three-column explorer layout. The default remains navy even with a light OS
appearance. The theme action switches between navy and light, updating its label
to describe the next action. Source overview/tree, knowledge graph, path-based
architecture, inventory, filters and source inspection share the same snapshot.

The original illustrative Java preview remains a design reference. Its request
flow is not copied into production: source paths and declarations do not establish
runtime calls, Spring bindings, Maven resolution or successful tests. The real
[generated HTML](../examples/aikya-memory-generated.html) contains 23 nodes and
27 explicit relationships. All 15 source hashes match the retained fixture at
`tests/fixtures/memory-viewer/aikya-java-validation/`.

The index, notes, publication protection, observer and local live server retain
their existing contracts. No model/API calls or external page requests are added.
English and Spanish READMEs explain the layout and the difference between source
hierarchy and runtime behavior. Changes remain under Unreleased; this task does
not select a new package release version.

## Observed local checks

Platform: macOS arm64, Python 3.13.2, isolated Chromium. Optional grammar wheels
were loaded from a temporary directory; no SDK or user credentials were needed.

| Check | Observed result |
|---|---|
| Complete regression suite | 593 tests run in 965.754 s: 590 passed and 3 environment-specific skips; zero failures/errors |
| Public executable command contracts | All 28 commands exercised; 52 process checks passed, including expected rejection cases |
| Final focused exporter tests | 13 passed |
| Version 2 browser acceptance | 19 checks passed against the final generated artifact |
| Live browser acceptance | 18 checks passed; new Java class appears without reload, retaining filters, selection and zoom |
| Additional theme/language acceptance | Five checks passed; light theme survives a live change and Spanish labels/actions render |
| Optional language suite | 3 passed, 1 dependency-free fallback check skipped; six language/dialect fixtures exercised |
| Example profiles | 14/14 passed |
| Final wheel and source archive | Build passed |
| Isolated final-wheel installation | Eight combinations passed: global/project × ODD/SDD × init/analyze; SDK absent |
| Clean installer on macOS | Global/project installation, update and uninstall passed without a checkout; custom files and referenced interpreters preserved |
| Agent/skill metadata and registration | Valid; 30 agents, 29 engineering skills and 28 public commands |
| Pinned documentation catalog | Valid; 120 templates and 155 reference files |
| Version/changelog and static context contracts | Valid; static context proxy 3,356 within the 6,000 limit (not measured billable tokens) |
| Changed Python source quality | Zero errors and zero duplicate groups; four existing/extended coordinator cohesion warnings |

The browser acceptance first ran against the previous generated report and
detected the absent version 2 default/theme action, source overview placement and
hierarchy behavior. The final run passes after the renderer changes. Keyboard
selection, source inspection, empty searches, reduced motion and widths 1560,
1024, 768 and 390 pixels are covered. No page errors, CSP failures or external
traffic were observed. Updated [desktop](../examples/aikya-memory-live-desktop.png)
and [mobile](../examples/aikya-memory-live-mobile.png) captures are retained.

## Reproduction

Use a contributor environment with the package installed, plus Playwright and
its Chromium for the optional browser check. Playwright is not a product runtime
dependency. `AIKYA_CHROMIUM_EXECUTABLE` can select an existing Chromium executable.
`AIKYA_BROWSER_REPORT` optionally saves the browser's JSON evidence.

```text
python -B -m unittest discover -s tests -q
python -B scripts/ci/command_acceptance.py --output <temporary>/commands.json
python -B scripts/ci/smoke_profiles.py
python -B scripts/ci/validate_agent_assets.py
python -B scripts/ci/check_assets.py
python -B -m aikya.documentation.templates check
python -B -m aikya.quality.source --changed --base origin/develop
node scripts/ci/memory_viewer_browser.cjs <absolute-generated-html>
python -B -m build --no-isolation --outdir <temporary>/dist
python -B scripts/ci/package_smoke.py --wheel <temporary>/dist/aikya_harness-7.0.1-py3-none-any.whl
python -B scripts/ci/build_installers.py --version 7.0.1 --output <temporary>/dist
python -B scripts/ci/installer_smoke.py --assets <temporary>/dist
```

The command battery executes local deterministic support contracts in disposable
projects. It does not claim that an authenticated assistant followed all slash
instructions, installed third-party skills or deployed infrastructure. Native
Claude Code validation remains in the user's separate environment. Remote CI
results must be assessed on the pull request; local macOS results alone do not
prove native Windows/Linux compatibility. The pull request must not be merged
by this task.

GENERATED BY AIKYA HARNESS
