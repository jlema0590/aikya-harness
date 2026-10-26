# Repository Cleanup Implementation Plan

> **For Aikya contributors:** Implement this plan task by task through the approved Aikya workflow. Preserve explicit user authorization and record observed results in the checkboxes.

**Goal:** Remove verified redundant artifacts, organize historical documentation and reduce unnecessary registered-runtime payload while preserving commands, compatibility, licenses and audit evidence.

**Architecture:** Use the per-file audit manifest as the baseline for safe operations. Separate exact duplicates from unique historical content and distribution-only examples; an absent import alone never authorizes deletion.

**Tech Stack:** Python 3.10–3.13 standard library, Git, unittest and the existing catalog/installation checks.

**Spec:** [Repository cleanup audit](../research/2026-10-23-repository-cleanup-audit.md) and its [per-file manifest](../research/2026-10-23-repository-cleanup-inventory.json). Baseline: 19111a1.

## Global constraints

- Preserve 27 public commands, all ODD/SDD approval boundaries and custom installed files.
- Keep all pinned Milkeles assets, licenses, manifests and migration byte signatures.
- Keep root entry-point contracts and functional technical-asset locations.
- New plans/reports use aikya/docs/; every authored Markdown ends with the Aikya footer.
- Do not mix source cleanup with the existing install.py refactor or automatically migrate user project documentation.
- Preview operations and verify baseline hashes before mutation. Preserve unique assets and history rather than assuming that unlinked means worthless.
- Execution authorized by the user after the audit. Cleanup results are recorded in ../validation/REPOSITORY_CLEANUP.md; the original audit remains a historical baseline.

## Review focus

- A duplicate may diverge after the audit; detect changed bytes and abort retirement.
- A historical proposal can represent unimplemented backlog; preserve its status and scope.
- A packaged gallery may be unnecessary for execution but still linked from runtime documentation; repair those references before omitting it.
- An apparently missing migration source can still supply trusted hashes for retired commands; retain compatibility records.
- Cache cleanup must stay inside known repository cache directories and reject symlinks or unrelated ignored user data.

### Task 1: Retire the verified duplicate and optionally purge local bytecode

**Files:** Remove Aikya-Harness.png only after a byte comparison with docs/images/aikya-harness.png; leave the referenced image and both README image links intact. Write aikya/docs/validation/REPOSITORY_CLEANUP.md.

- [x] Preview baseline hash and incoming references; require the root image and retained image to remain byte-identical. Do not delete the unique Spanish image as part of this exact-duplicate operation.
- [x] Retire the redundant tracked root copy using Git so its prior bytes remain recoverable.
- [x] If cache cleanup is requested during execution, enumerate only ignored __pycache__ bytecode files in the repository, reject symlinks and preserve all other ignored data. Perform this after tests because Python may recreate caches.
- [x] Check README links, the retained image and the release/source archive contents. This reversible asset-only change does not need a new implementation-mirroring test.

### Task 2: Archive unique media provenance and historical plans/evidence

**Files:** Move the reviewed unique graphic/prompt, seven docs/plans files and ten docs/validation files into the existing canonical plan/images/validation structure; update links, archive status and indice.md through the shared document writer.

- [x] Preserve a verified archival copy of trazabilidad-documental.png before deciding whether it remains in the active README image collection. Preserve the 344-byte edit recipe as manual provenance if useful.
- [x] Label superseded external-provider/SDD preview plans as historical. Keep MULTIPLATFORM_CODEX_COPILOT.md as an unimplemented proposal, not a completed feature.
- [x] Preserve historical test results and recorded baselines without updating them to pretend old acceptance used the new implementation.
- [x] Integrate with the approved document-consolidation mapping, preflight source/destination hashes, repair relative links and rebuild the exact canonical index. Remove only empty managed directories.

### Task 3: Keep the historical gallery in source, trim the runtime payload

**Files:** Modify aikya_setup.py files_to_copy, affected runtime guide references and tests/test_agent_loop_installation.py or a focused tests/test_runtime_payload.py. Keep examples/documentation/generated/ and its manifest in the source repository.

**Interfaces:** The registered runtime inventory omits only the explicitly historical generated gallery; template/catalog assets and fixture profiles needed by supported workflows retain their paths. Do not maintain a second divergent CORE_FILES list.

- [x] Add a failing behavioral test that registers a runtime without the generated gallery and launches init/analyze from an unrelated cwd. Assert actual outcomes and needed template availability, not the text of the filtering code.
- [x] Extend the existing eight-case probe to three project types, two locales, two scopes and both ODD/SDD workflows; preserve live-SDK tests as separately opt-in.
- [x] Apply one shared distribution policy; update runtime-local gallery references to an explicit source-repository location or omit the irrelevant guide. Keep source-gallery links working.
- [x] Verify actual upgrades from the baseline. Do not automatically delete an old runtime gallery if it contains modified user material; preserve or retire only recorded managed bytes with backups.
- [x] Measure resulting file count/bytes and run installation, asset, catalog and full regression checks.

### Task 4: Resolve stale documentation and helper candidates within their owning work

**Files:** Review examples/documentation/generated/README.es.md and snapshot metadata; review aikya_layout.module_root and runtime_metrics.resolve_actor_model within their existing refactor scopes.

- [x] Choose a coherent historical archive or refresh for the pre-ODD gallery. Preserve synthetic flags and manifest hashes; never rename one command in a checksummed snapshot while reporting the old manifest as current.
- [x] Handle the synthetic fixture-evidence link as example provenance. Preserve the two illustrative pinned ADR links in upstream reference templates.
- [x] Characterize public/helper compatibility before integrating or deprecating the two functions with no production callers found. Their containing modules remain active and must stay.
- [x] Review the twelve legacy/root/example Markdown footer cases independently of the 59 engineering assets already stamped at installation; do not treat formatting differences as unused assets.

### Task 5: Verify and publish the actual cleanup evidence

- [x] Run unittest discovery on the supported Python matrix, 14 example profiles, asset/frontmatter checks, catalog checksums, gallery manifest integrity and link/index checks.
- [x] Verify the five retired-command hash records and historical fixtures still support upgrade/retirement tests.
- [x] Record exactly which paths were removed, archived, retained or excluded from runtime distribution, with before/after bytes and preserved source hashes.
- [x] Report source-quality findings truthfully: the separate install.py modularization remains pending until its own plan is completed.
- [x] Keep implementation local for review; no new commit/push/publication was requested with this execution. Earlier audit-only publication remains separate.

## Execution notes

Completed locally with the observed results in [cleanup validation](../validation/REPOSITORY_CLEANUP.md). The two helper candidates were characterized and retained; the gallery was coherently archived rather than regenerated; the twelve footer cases were normalized. The historical synthetic link remains explicitly documented provenance. Only the nineteen audited historical/media paths were relocated, using the consolidation plan’s canonical categories. Broader guide migration, runtime path enforcement and install.py/package restructuring are separate pending plans, not hidden checklist completions.

GENERATED BY AIKYA HARNESS
