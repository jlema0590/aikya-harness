# Memory interactive graphs — local acceptance

Date: 2026-10-29. Version: **7.1.1**. Branch: `feat/memory-interactive-graphs`.
Base: `origin/develop` at `177f032`. All browser data in this report is synthetic.

## Result

Inventory now hides the SVG through its actual `hidden` attribute. Rows receive
real clicks, remain keyboard accessible and retain 100/100/75 pagination in the
275-node fixture. The original failing interaction reproduced the SVG intercepting
row clicks; the acceptance checks now exercise visibility and interaction rather
than just counting rows.

Knowledge graph and Architecture offer progressive expansion, readable labels,
pan, anchored zoom, fit, per-view reset and individually draggable objects.
Architecture reserves space by subtree. Small graphs use bounded relaxation;
dense graphs use spatial placement with stable previous positions and priority
for manual pins. Labels account for component radius at high zoom. Full source
names and paths remain available through the inspector and accessible titles.

Arrow keys move a focused node by ten screen pixels. Escape, pointer cancellation
and view changes cancel an active drag in its original view. Manual positions and
cameras survive filtering, view changes and live snapshots while the page stays
open. Reloading resets those visual positions. They never change the index,
source files or signed report.

Verified containment connections show directed travel; other relations use a
neutral pulse. Incoming inspector entries retain their actual source and target.
The 80-connection animation budget is calculated before the 3000-edge drawing
limit, including initial traces. Drawing omissions and grouped nodes have explicit
counts; search and Inventory still reach sources outside the drawing limit.
Motion-off, reduced motion, dragging and background visibility pause effects.
These effects represent indexed relationships, not observed runtime execution.

The modules remain embedded in one CSP-hashed offline script. The publication
fingerprint includes every viewer resource. A renderer update republishes matching
HTML/report hashes without changing source data; an unchanged second export does
not rewrite the pair. Existing ownership and edited-report protections remain.

## Observed verification

| Check | Observed result |
|---|---|
| Full Python regression in an isolated child environment | 630 tests, OK, 2 skipped, 959.667 s |
| Final Memory Python regression after presentation refinements | 49 tests, OK, 27.961 s |
| Pure layout tests | 6 passed, 0 failed |
| Browser interactions, source English / Spanish / installed wheel | 48 + 48 + 48 checks passed |
| Existing viewer browser acceptance, English / Spanish | 21 + 21 checks passed |
| Dense, deep, interrupted and synthetic live acceptance | 20 checks passed |
| Final wheel installation smoke | 8 cases passed; global/project × ODD/SDD × init/analyze |
| Parser-free installed wheel | Missing-package fallback and module impersonation tests passed; 2 grammar-only tests skipped |
| Native PowerShell installer suite through a portable local runtime | 10 tests passed, no skips |
| Wheel and source distribution | Built successfully for 7.1.1 |
| Agent/skill assets and documentation template catalog | Valid; 120 templates and 155 reference files |
| Final changed-source quality check | 10 files; no errors, warnings or duplicate blocks |
| Documentation and whitespace | Changed Markdown footers and index entries verified; diff whitespace clean |

The six browser runs contain **206 successful checks**. Offline runs record no
external requests and all runs record no JavaScript/CSP errors. Synthetic live
requests are fulfilled in-process by Playwright; no private project server is used.
The checks include a relation-only live change with unchanged node IDs, preserved
camera/manual positions, addition and deletion while Inventory stays exclusive.

The full Python suite completed before the final JavaScript/CSS refinements for
dense placement, high-zoom labels and initial trace budgeting. The final 49 Memory
tests, all six browser runs, layout tests, rebuilt distributions and eight wheel
installation cases validate the final assets. Python production code did not
change between those runs.

The full suite's two skips were the parser-free fallback (grammar extras were
installed) and native PowerShell (not on the default PATH). Separate runs exercised
both paths. The parser-free run's grammar-only skips were exercised in the full
environment with extras. This is not a claim of native Windows execution.

Development runs exposed personal Claude configuration contamination, sandbox
loopback limits and source-copy preflight guards while files were still changing.
A discarded home monkeypatch and inherited `PYTHONPATH` also contaminated test
fixtures. Final acceptance uses a separate child-process home and storage,
clears inherited import-path overrides and leaves production approval, ownership
and integrity checks enabled. No personal settings were modified.

## Receipts and examples

- [Interactive, offline 275-node example](../examples/aikya-memory-interactive.html)
- [Knowledge graph, navy](memory-interactive-graphs/graph-navy.png),
  [Architecture](memory-interactive-graphs/architecture.png),
  [Knowledge graph, light](memory-interactive-graphs/knowledge-graph.png)
- [Layout TAP results](memory-interactive-graphs/layout.tap)
- [English interactions](memory-interactive-graphs/interactions-en.json),
  [Spanish interactions](memory-interactive-graphs/interactions-es.json),
  [installed-wheel interactions](memory-interactive-graphs/installed-wheel-browser.json)
- [English viewer checks](memory-interactive-graphs/viewer-en.json),
  [Spanish viewer checks](memory-interactive-graphs/viewer-es.json),
  [density and live checks](memory-interactive-graphs/density-live.json)
- [Eight installed-wheel cases](memory-interactive-graphs/wheel-installation.json)
- [Approved plan and implementation record](../plan/2026-10-28-memory-inventario-superpuesto.es.md)

The committed example and installed-wheel fixture are byte-identical. Their
SHA-256 is `3504b348f732870d48e0ccc35cd749e2b179eedc2e0c50ec452b7f613b250940`.
The package smoke explicitly reports no checkout imports and no installed SDK.
No model calls were needed to maintain or visualize this memory.

Local environment: macOS arm64, Python 3.13.18, Node 24.22.1, Playwright 1.62.1,
Chromium 151.0.7922.34. The recorded 500-node layout test took **10.28 ms**;
the rejected quadratic version took about 815 ms on this machine. This measures
layout computation, not GPU frame time or a cross-device animation guarantee.
The browser also enforces a ten-second dense-fixture loading ceiling.

## Reproduction

Use a supported Python contributor environment with the package installed, build
tools, optional parser extras for language coverage, and contributor-only
Playwright/Chromium. The browser CI job pins Playwright and runs on Ubuntu/Node 22.

```sh
python scripts/ci/run_isolated_tests.py
python scripts/ci/run_isolated_tests.py --pattern 'test_memory_*.py'
node --test tests/memory_layout.test.cjs
for language in en es; do
  python tests/memory_viewer_fixture.py "/tmp/memory-$language.html" --language "$language"
  node scripts/ci/memory_viewer_browser.cjs "/tmp/memory-$language.html"
  node scripts/ci/memory_interactions_browser.cjs "/tmp/memory-$language.html"
done
for shape in mixed flow80 flow81 flow-overflow wide deep; do
  python tests/memory_viewer_fixture.py "/tmp/memory-density/$shape.html" --shape "$shape"
done
python tests/memory_viewer_fixture.py /tmp/memory-density/live.html --live
node scripts/ci/memory_density_browser.cjs /tmp/memory-density
python -m build --no-isolation
python scripts/ci/package_smoke.py --wheel dist/aikya_harness-7.1.1-py3-none-any.whl
python scripts/ci/validate_agent_assets.py
python -m aikya.documentation.templates check
python -m aikya.quality.source --changed --base origin/develop
```

## Publication and practical limits

The branch and commit are local; this task has not pushed a branch, created a
remote PR or published a release. Remote CI is therefore pending. Real project
HTML, notes and indexes were not modified. Native Windows/Linux browsers and
real SDK/model sessions were not exercised locally.

After installing the published update, regenerate an existing report through
`/aikya-memory --refresh`. Restart an observer/server still running the previous
runtime, then reopen the report. Reloading an older standalone HTML does not
replace its embedded resources. Preserve customized-report protection rather
than forcing an overwrite. Existing-project rollout remains pending publication.

## Prepared PR description

Title: **Fix Memory Inventory overlap and add interactive graph layouts**

Target: `develop`.

Inventory's SVG remained visible over rows and intercepted interactions. Reflect
its visibility attribute correctly, and replace compressed graph layouts with
progressive expansion, readable labels, draggable objects and per-view cameras.
Add bounded local connection animation, reduced-motion support and stable live
updates while preserving signed offline publication and source provenance.

Prepare v7.1.1 with bilingual README guidance, an offline example, synthetic
browser CI and recorded acceptance. Validation: 630 Python tests with two
environment skips covered separately; final 49 Memory tests, six layout tests,
206 browser checks, rebuilt distributions and eight installed-wheel cases passed.
Remote CI and real-project rollout remain pending.

GENERATED BY AIKYA HARNESS
