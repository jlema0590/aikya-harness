# Contextual composition of Aikya and Aikya reference collection foundations

Aikya now selects a documentation composition by public command, validated project
type, selected methodology and actual mobile platforms. It combines Aikya acceptance
and traceability with populated sections from the pinned Aikya reference collection templates. The
adapter never executes template advice, infers repository behavior, approves work
or certifies test results. Clearer acceptance is supported; user adoption is not
claimed to have been measured.

## Selection and output

| Workflow | Automatic default | Conditional document choices |
|---|---|---|
| /aikya-init | Existing Aikya overview plus Aikya reference collection onboarding navigation/workflow sections; profile-backed architecture; declared testing strategy | Only docs supported by onboarding decisions are created |
| /aikya-init with SDD | Same onboarding composition plus SDD guide/runtime | Specification packet starts with real /aikya-specify input, not initialization |
| /aikya-analyze | Existing-project context/architecture and observed test paths | Preview remains read-only; unsupported reports are omitted |
| /aikya-arc-review | Read-only architecture recipe | Explicitly requested architecture updates; distinct ADR/design documents only when justified |
| /aikya-feature, ODD | Aikya objective + observable acceptance + optional Aikya reference collection technical-design sections in features/<slug>/spec.md | feature/api/database/spec context; optional separate design/decision if needed |
| /aikya-mobile-feature, ODD | Same acceptance composition with actual platforms in scope | Rejects profiles without mobile; platform-specific acceptance/checks must be supplied |
| /aikya-bugfix, ODD | Aikya reference collection bug-report register adapter in bugs/bugs.md | Append-safe real BUG-NNN report with mandatory reproduction |
| /aikya-feature, /aikya-mobile-feature, /aikya-bugfix under SDD | Dedicated SDD task authorization/implementation | No parallel ODD feature specification |
| /aikya-specify | Dedicated SDD engine; feature/api/database/spec selected from the actual change | Clarifications only when questions exist |
| /aikya-plan | Existing SDD design.md and plan.md | Optional Aikya reference collection goals, non_goals and open_questions in design sections |
| /aikya-tasks and /aikya-implement | Existing SDD tasks.md/state.json and approvals | Optional out_of_scope and constraints on each task; no extra task-plan file |
| /aikya-tests, ODD | Aikya reference collection strategy composition in plan/testing.md | Manual cases in plan/test-cases/<slug>.md; requested results in quality/test-reports/<slug>.md |
| /aikya-tests under SDD | Dedicated explicit evidence-recording action | Explicit strategy/case/summary roles remain available outside SDD state; none approves an SDD stage |
| /aikya-sdd-status | Read-only status selection | Explicit actual verify input can populate evidence/verification records with assessment/residual risk |

The registered test command remains /aikya-tests. SDD is a methodology for the three
existing project types, not another project type. Selecting a reference never
adds a framework, platform, dependency or deployment capability.

## Plan without writes

The installed adapter reads the actual profile; it does not fabricate one:

```sh
python3 aikya/scripts/harness/documentation_workflows.py plan --root . --command aikya-feature
python3 aikya/scripts/harness/documentation_workflows.py plan --root . --command aikya-feature --kind api
python3 aikya/scripts/harness/documentation_workflows.py plan --root . --command aikya-tests --document summary
```

The public skills invoke this selection during their existing workflows. The plan
returns engine, primary document, references and permitted document roles. These
commands are read-only, including bytecode behavior. Before a profile exists, init
uses the onboarding interview; approved installation runs the bootstrap adapters.

## Reviewed hybrid input

For an ODD feature, provide title, objective, a nonempty acceptance list and
only known, populated Aikya reference collection technical-design section keys. Example inputs and
rendered English/Spanish outputs are under examples/documentation/composed-feature.*.
They are synthetic fixtures and not real project facts.

```json
{
  "title": "Synthetic lookup example",
  "objective": "Fixture example: preserve the lookup response.",
  "acceptance": ["The missing fixture ID returns the agreed response."],
  "sections": {
    "context-and-scope": "Only the fixture lookup boundary is in scope.",
    "alternatives-considered": "A separate service would add unnecessary fixture state."
  }
}
```

```sh
python3 aikya/scripts/harness/documentation_workflows.py write --root . --command aikya-feature --slug lookup --input reviewed.json --approved
```

The agent identifies the change context and supplies --kind when appropriate; no
semantic inference from arbitrary prose is claimed. The default hybrid output has
objective, stable visible AC labels, actual mobile platforms for the mobile command,
populated foundation sections and source references. It omits unavailable rollout,
owner, risk and other content rather than filling them from upstream examples.

Known foundation keys come from the pinned catalog; rendered labels are provided in
en/es by Aikya. User-supplied values are preserved. Fields can contain H3 subheadings
and balanced fenced examples; competing H1/H2 headings and unclosed fences are
rejected before writes. This prevents data fields from replacing acceptance sections.

## Safe updates and conditional reports

On an existing generated document, only supplied H2 sections are replaced; other
sections and fenced examples are retained. Ambiguous duplicate headings or unclosed
existing fences require review. Custom documents, symlinks and custom or unindexable
navigation prevent writes before content changes. The adapter uses fixed canonical
destinations, requires lowercase slugs, writes the terminal footer once and refreshes
indice.md. Shared overview and strategy stay at their existing paths. For ODD feature requests, an actually changed substantive features/<slug>/spec.md plus its request log satisfies the feature documentation gate; unchanged old specs do not. Existing catalog/roadmap coverage remains compatible.

For an ODD test report, select --document summary and provide what-was-tested,
assessment and an evidence list of existing nonempty, contained, nonsymlink files.
The report says outcomes were supplied and not independently executed by the adapter.
It grants no release approval and changes no SDD state. Use --document case only when
manual cases help; merely running tests does not require all report types.

## SDD composition

Specification, plan and task approvals continue to be independent, explicit gates.
The documentation adapter rejects generic writes that would bypass the selected SDD
workflow. It does not write specs/, approvals or state.json. Design/task/evidence
foundation fields are validated, rendered and retained by the existing SDD engine:

- design.sections: goals, non_goals, open_questions, in addition to existing fields.
- each task.sections: out_of_scope, constraints, in addition to existing fields.
- verification.sections: assessment, residual_risk, in addition to existing fields.

There is one authoritative design, task list and evidence record per specification.
Optional fields do not create empty reports. Source notes respect the living-doc
language; offline starter assets and engineering instructions stay English.

## Scope and provenance

The adapter actively composes onboarding, architecture, technical design, ADR,
testing strategy, manual cases and requested test summaries. Other Aikya reference collection
foundations remain available through the reviewed catalog when their purpose is
relevant; the thirty documents are not all generated during onboarding.
The pinned upstream library and MIT license remain unchanged by this composition.
Aikya reference collection is the only external template provider. Aikya owns the acceptance IDs,
required fields, safe writing and approval contracts. See DOCUMENTATION_TEMPLATES.md
for the full catalog and SDD_TEMPLATES.md for the engine contract.

GENERATED BY AIKYA HARNESS
