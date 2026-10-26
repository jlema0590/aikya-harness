# Aikya reference collection templates in Aikya SDD

Aikya composes nine existing SDD roles using only the pinned Aikya reference collection library.
The source structures guide drafting; requirement IDs, compatibility fields,
traceability and separate approvals belong to Aikya. The local engine does not
execute upstream examples or require every optional section.

## Template mapping

| Name | Library asset | Aikya workflow and output |
|---|---|---|
| `feature` | `feature.spec.md` | `/aikya-specify`: populated feature sections in `spec.md` |
| `api` | `api.spec.md` | `/aikya-specify`: populated endpoint/consumer contract in `spec.md` |
| `database` | `database.spec.md` | `/aikya-specify`: populated data/migration contract in `spec.md` |
| `spec` | `spec.md` | `/aikya-specify`: general change proposal in `spec.md` |
| `design` | `design.md` | `/aikya-plan`: decisions and interfaces in `design.md`; execution/testing in `plan.md` |
| `tasks` | `tasks.md` | `/aikya-tasks`: requirement/dependency links plus reviewed scope and checks |
| `evidence` | `evidence.md` | `/aikya-sdd-status`: recorded existing evidence; created after verification input |
| `review` | `review.md` | Explicitly requested review notes for an existing specification |
| `constitution` | `constitution.md` | Explicitly requested engineering rules for the active SDD project |

The sole external template provider is Aikya reference collection at commit
35fc8e29be1f0093b8ef13a9762de67dc99b6882. Paths below are relative to its root:

| SDD role | Aikya reference collection reference |
|---|---|
| feature | general-swe/requirements/product-requirements-document.md |
| api | general-swe/foundations/interface-control-document.md |
| database | general-swe/foundations/data-model.md |
| spec | ai-assisted-development/specification/agent-task-specification.md |
| design | general-swe/foundations/technical-design-document.md |
| tasks | ai-assisted-development/foundations/task-plan.md |
| evidence | general-swe/foundations/test-summary-report.md |
| review | general-swe/foundations/code-review-guidelines.md |
| constitution | ai-assisted-development/foundations/agent-instructions-file.md |

These are adaptations to Aikya's existing input contracts, not byte-for-byte copies
of filled-in upstream examples. The source note in each generated role records its
exact pinned URL. API/database specialization does not add new project types.

The library lives at `aikya/scripts/harness/sdd-templates/` in an initialized SDD
project and at `sdd-templates/` in the registered runtime. It is not copied as nine
empty project reports. Selecting SDD creates a guide at `aikya/docs/specs/README.md`;
actual specification documents appear only as reviewed content becomes available.

## Read-only discovery

Use the public slash workflows in Claude Code. Maintainers can inspect the internal
adapter without a project profile or network access:

```text
python3 aikya/scripts/harness/sdd_engine.py templates --root .
python3 aikya/scripts/harness/sdd_engine.py templates --root . --template api
```

The first command lists exact section keys and attribution. The second prints the
selected English starter without creating files. Library assets remain English;
project document headings follow the configured en/es policy. Supplied text is
preserved rather than automatically translated or replaced by illustrative examples.

## Reviewed specification input

Existing JSON remains valid. To choose a specialized template, supply `template`
(`spec`, `feature`, `api` or `database`) and optional `sections`. Section values must
be nonempty text, at most 4000 characters each and 20000 characters together.
Unknown template names/keys and non-text values are rejected before writes.

This is an illustrative input, not a claim that the endpoint already exists:

```json
{
  "id": "SPEC-001",
  "title": "Reviewed item lookup contract",
  "objective": "Define missing-item lookup behavior.",
  "template": "api",
  "sections": {
    "endpoint": "GET /items/{id}",
    "responses": "An unknown item returns the agreed not-found response.",
    "compatibility": "Retain the currently approved error envelope."
  },
  "requirements": [{
    "id": "REQ-001",
    "description": "Missing-item errors remain stable.",
    "acceptance": ["Given an unknown identifier, the response follows the reviewed error contract."]
  }],
  "questions": [],
  "nonfunctional": []
}
```

`/aikya-plan` accepts `sections` from the design template. Each task can carry
`sections` from the tasks template, including `allowed_files`, `checks`, `owner`
and `done_when`. Verification input accepts evidence-template sections. These are
retained in versioned `state.json` and revalidated on later loads. Omitted sections
are not rendered as empty headings. Approved stages remain immutable.

Task scope/check text guides the authorized agent; it is not an operating-system
sandbox and is never automatically executed. Requirement evidence retains Aikya's
existing requirement-ID granularity. Record individual acceptance outcomes in the
supporting checks rather than claiming the engine proved their content.

## Review and engineering constitution

Only explicitly reviewed, nonempty content can create these optional documents:

```text
python3 aikya/scripts/harness/sdd_engine.py document --root . --template review --id SPEC-001 --input reviewed-notes.json --approved
python3 aikya/scripts/harness/sdd_engine.py document --root . --template constitution --input reviewed-rules.json --approved
```

Inputs use `{"sections": {...}}` with the selected catalog's keys. Review notes go
in the active specification's `review.md`; team rules go in
`aikya/docs/specs/constitution.md`. These operations do not approve a workflow
stage, alter task status, execute checks or authorize deployment.

## Preservation and evidence

Every generated Markdown document ends with `GENERATED BY AIKYA HARNESS`.
Legacy Aikya SDD ownership markers remain recognized; customized documents,
symlinked paths and customized indices require review rather than replacement.
SDD saves refresh `indice.md` from actual files. Code/config/JSON and original
migration backups keep their respective formats and original bytes.

`verification.md` and `evidence.md` appear when actual requirement evidence is
recorded. Task progress invalidates a prior verification record; existing reports
then state that their results are no longer current. No verification report is
created just to hold an empty result. A clarification document is created when
there are real questions to resolve.

Structural validation and a recorded passing result do not prove command execution.
The engine retains `independently_executed: false`; report separately performed
checks and unavailable tooling. Existing approval, scope and remote-operation
permissions continue to apply regardless of the selected template.

## Contextual Aikya composition

Public workflows now select and compose reviewed foundations with Aikya acceptance, onboarding and testing documents. SDD keeps its existing records and approval gates. See [selection, input examples and preservation behavior](CONTEXTUAL_TEMPLATE_COMPOSITION.md).

## Updating existing installations

Known predecessor runtime, catalog and starter bytes upgrade with backups. A customized coupled template asset blocks installation during preflight, before any project mutation; review that customization before updating the generator and its catalog together. Existing project records and CLAUDE.md remain preserved. Historical audit notes describe their original snapshot and are not active template providers.

GENERATED BY AIKYA HARNESS
