# Public command and documentation-path validation

Version 6.1.1, branch `feat/sdd-spec-coding-templates`, 2026-10-23. This checkpoint includes the previously local cleanup and Python package structure. The SDD engine remains 658 lines at this checkpoint; its modularization is the next, separately validated step after publishing.

## Observed results

- All 27 public Claude command support contracts passed: 49 actual local process invocations across disposable new/existing projects, ODD/SDD, development, mobile and infrastructure cases. Inputs and usage samples are explicitly controlled fixtures.
- 495 regression tests passed on each Python version 3.10, 3.11, 3.12 and 3.13. The suite includes 48 onboarding combinations: two scopes, three project types, two methodologies, two locales and init/analyze.
- All 14 versioned example profiles passed; bundled command/agent/skill metadata and all 120 templates (155 checked reference files) passed integrity checks.
- A built wheel passed eight isolated onboarding cases, with no source-checkout imports and no optional SDK installed. Both distributions built successfully; the wheel contains no removed source-resource directory.
- Four upgrades from published baseline `08db487` passed: global/project registration and initialized ODD/SDD projects. The new library exists, the old active directory is gone, and the controlled custom locale adapter remains unchanged.
- Rename regressions cover exact-byte backup/retirement, custom-content rejection before writes and restoration after an injected ownership-manifest write failure. The initial failing cases were observed before implementation.
- A separate pre-refactor characterization passed six type/locale cases and retained 78 lifecycle/document fingerprints for the next step.

## Markdown destinations

Every generated living Markdown file in the five acceptance projects passed canonical-layout, terminal-footer and exact-index validation. No root docs/, plans/, plan/, bugs/ or features/ directory was created. The detailed per-command changes and complete living/technical file inventories are in COMMAND_ACCEPTANCE_RESULTS.json.

| Operation | Verified destination or behavior |
|---|---|
| Init / analyze | `aikya/docs/overview.md`, `architecture/architecture-overview.md`, `plan/testing.md` when supported, tools/skills policy documents and `indice.md` |
| Feature / mobile feature, ODD | `aikya/docs/features/lookup/spec.md`; unsupported or empty sections are omitted |
| Bugfix | `aikya/docs/bugs/bugs.md`; a duplicate BUG ID is rejected without altering the register |
| Docs / docs sync | `aikya/docs/plan/acceptance.md` and `aikya/docs/indice.md`; missing approval and traversal are rejected |
| Specify / clarify | `aikya/docs/specs/development/SPEC-001/spec.md` and `clarifications.md` |
| Plan / tasks | The same SDD dossier contains `design.md`, `plan.md` and `tasks.md`; stage approval gates are enforced |
| Implement / SDD status | Authorization and persisted state inspection; the tested incomplete workflow does not produce a passing verification report |
| Install skill | Missing explicit authorization is rejected; no `tools/skill-comparison.md` is fabricated |
| Read-only planning / inspection | No living documentation write is inferred from an inspection command |

Functional instruction assets such as root CLAUDE.md, `.claude/` skills/rules and the installed offline runtime remain outside living docs by design. Analyze also retains its technical `.aikya/analysis/report.md` contract. These are inventoried separately rather than misreported as misplaced project records.

## Template naming and provenance

Canonical source: `src/aikya/resources/aikya-template/docs/`. Installed runtimes use `aikya-template/docs/` beside their Python adapters. Public rendered references use that namespace. Original copyright, MIT license, upstream source hashes/URLs and NOTICE remain in the provenance records; historical reports, example galleries and migration signatures retain their original identities. Removing branding does not erase attribution or rewrite past evidence.

The path receipt records 157 moved catalog assets. New template IDs and supported project types remain unchanged. The legacy Python adapter name `documentation_templates.py` remains compatible; it is not an old resource directory.

## Limits and findings

No authenticated model dialogue, external skill download, dependency installation or infrastructure deployment was performed. These checks execute the local tools behind declarative slash commands; they do not claim a live Claude session. The existing fake-provider loop, permissions, memory and adversarial suites remain part of the regression run.

The first general regression pass exposed four obsolete branding expectations in tests; these were updated to assert the new namespace, then the full matrix passed. Acceptance-runner setup corrections followed existing CLI contracts; no application failure was hidden as a passing check.

Two unresolved local links are retained intentionally: an upstream illustrative decision and a historical generated example referencing an unavailable synthetic log. Placeholder links containing template variables are excluded from the navigation check. No additional broken navigation link was observed.

Reproduce: `python3 -B scripts/ci/command_acceptance.py --output /tmp/aikya-command-acceptance.json`, followed by `python3 -B -m unittest discover -s tests`. Wheel validation uses `scripts/ci/package_smoke.py`.

GENERATED BY AIKYA HARNESS
