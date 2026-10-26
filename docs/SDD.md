# Spec-Driven Development in Aikya 6.1.1

SDD is an explicit methodology over the existing `development`, `infrastructure`
and `devops` project types. It is not a replacement for Clean Architecture,
microservices or another application architecture. Standard mode remains the default.

## Enable SDD

For a new project, use `/aikya-init` and select `sdd` during the interview. For an
existing repository, preview `/aikya-analyze --dry-run --methodology sdd --docs-lang en`,
review the proposed files and approve adoption. The command adapter must carry the
same methodology and locale to the approved operation. Existing SDD choices are
retained during refresh. Disabling SDD is a separate migration, not a silent refresh.

Installation retains `/aikya-analyze`, `/aikya-models` and `/aikya-tokens` and adds
six commands, for 28 public commands in total. Global and project registration remain
separate from initializing or adopting a target project.

## Workflow and inputs

Run public slash commands inside Claude Code. The examples below document the
internal engine API for maintainers; they are not an alternative automatic installer.
Paths are relative to the active project, not the shared global runtime.

| Stage | Public command | Reviewed JSON input | Approval |
|---|---|---|---|
| Specify | `/aikya-specify` | id, title, objective, requirements, nonfunctional, questions | Explicit permission to write the draft |
| Clarify | `/aikya-clarify` | answers mapping existing questions to responses | Separate specification approval |
| Plan | `/aikya-plan` | design, testing, decisions, risks | Separate plan approval |
| Tasks | `/aikya-tasks` | tasks with id, description, requirements, depends_on | Separate task approval |
| Implement | `/aikya-implement` | Active SPEC-NNN and TASK-NNN | Consent for actual file changes |
| Inspect/verify | `/aikya-sdd-status` | Declared command, result and existing evidence file per requirement | Record actual observed results |

Requirements use unique REQ-NNN, INF-NNN or DEVOPS-NNN identifiers with non-empty
acceptance criteria. Tasks use TASK-NNN, cover all requirements and form an acyclic
graph. See [development](../examples/sdd/development/order-api/README.md),
[infrastructure](../examples/sdd/infrastructure/aws-network/README.md) and
[DevOps](../examples/sdd/devops/kubernetes-release/README.md) fixtures. Their environment
answers are examples, not authority to invent values or deploy resources.

The internal CLI exposes `new`, `clarify`, `approve`, `plan`, `tasks`, `worklist`,
`authorize`, `progress`, `verify`, `status`, `list`, `lint` and `completion`:

```text
python3 aikya/scripts/harness/sdd_engine.py new --root . --input reviewed-spec.json
python3 aikya/scripts/harness/sdd_engine.py clarify --root . --id SPEC-001 --input reviewed-answers.json
python3 aikya/scripts/harness/sdd_engine.py approve --root . --id SPEC-001 --stage spec --actor reviewer
python3 aikya/scripts/harness/sdd_engine.py plan --root . --id SPEC-001 --input reviewed-plan.json
python3 aikya/scripts/harness/sdd_engine.py approve --root . --id SPEC-001 --stage plan --actor reviewer
python3 aikya/scripts/harness/sdd_engine.py tasks --root . --id SPEC-001 --input reviewed-tasks.json
python3 aikya/scripts/harness/sdd_engine.py approve --root . --id SPEC-001 --stage tasks --actor reviewer
python3 aikya/scripts/harness/sdd_engine.py authorize --root . --id SPEC-001 --task TASK-001
python3 aikya/scripts/harness/sdd_engine.py progress --root . --id SPEC-001 --task TASK-001 --result done --evidence actual-check.log
python3 aikya/scripts/harness/sdd_engine.py verify --root . --id SPEC-001 --input actual-verification.json
python3 aikya/scripts/harness/sdd_engine.py completion --root . --id SPEC-001
python3 aikya/scripts/harness/sdd_engine.py lint --root .
```

Each `approve` invocation requires an actual preceding user approval; an actor
string is a local attribution record, not authenticated identity or a signature.
Plan/task approval cannot authorize downloads, infrastructure apply/destroy,
remote cluster writes or publication. Those require separate scoped authorization.

## Active generation context

In SDD mode, application and infrastructure generation require both `--spec-id`
and `--task-id` for the selected approved task. Authorization checks the current
profile, all three approved stages, the actual task and completed dependencies.
A historical approved specification does not unlock a different pending task.

```text
python3 aikya/scripts/harness/scaffold.py apply --yes --spec-id SPEC-001 --task-id TASK-001
python3 aikya/scripts/harness/infrastructure.py generate --approved --spec-id SPEC-001 --task-id TASK-001
```

Use these mutation commands only after reviewing and approving their concrete
plans. Scaffolding can invoke external generators; infrastructure generation only
prepares local artifacts and is distinct from deployment. Existing-project source
changes use the authorized implementation task instead of new-project scaffolding.

## Files and language

```text
aikya/docs/specs/<project_type>/SPEC-NNN/
  spec.md
  clarifications.md
  design.md
  plan.md
  tasks.md
  verification.md
  evidence.md         # after recorded verification
  review.md           # optional reviewed notes
  state.json
```

Files appear as the lifecycle advances. Markdown headings follow the project's
existing en/es living documentation policy; user-authored content is preserved.
Machine IDs, schema keys, statuses and engineering instructions remain English.
`state.json` is deliberately versioned alongside the Markdown. Preserve both in
Git; Markdown alone cannot reconstruct approvals or task progress.

Approved artifacts cannot be edited through the workflow: create a new specification
to change scope. Every load and lint rechecks persisted state for malformed shapes,
unknown references, missing coverage, cycles and inconsistent approvals/progress.
Lint also rejects missing state/documents, missing evidence files and symlinked paths.

## Structural validation versus completion

`lint` is a structural and traceability check: an empty SDD workspace or a valid draft
can pass without being complete. `completion --id SPEC-NNN` additionally requires
approved stages, completed tasks and a passing evidence record for every requirement.

Verification JSON has this shape:

```json
{"requirements":[{"id":"REQ-001","command":"the actual executed check","result":"passed","evidence":"relative/path/to/actual-check.log"}]}
```

Use `failed` for an actual failed check. Evidence paths must exist inside the project.
`EVIDENCE_RECORDED` and completion readiness do not certify command execution:
the engine does not run or interpret supplied commands/logs, and records
`independently_executed: false`. Report separately executed quality/build/test
results and unavailable tools. Do not use structural lint as a release-success signal.

Records are local, editable, single-writer files. Evidence contents are not hashed
or cryptographically bound to a commit. They are not immutable audit trails,
authenticated approvals or a durable concurrent transaction system. Multi-writer
coordination and stronger evidence provenance are outside this version's scope.

## Upgrades and customization

SDD activation preflights known engine/generator assets and the quality manifest
before writes. Exact supported old assets are upgraded with backups under
`.harness/backup-v611/`. Custom generators, customized SDD checks, symlinked paths
and incompatible manifests block activation for review instead of being replaced.
Existing team checks remain in `harness.json`; the required `sdd:traceability` check
is added once. Installation previews list supported upgrades and backup paths.

The legacy schema-1 format and exact 6.0.0 generated document ownership marker remain
readable when their contents satisfy current validation. Existing malformed records
need review; preservation is not permission to bypass the stricter checks.

Reverting harness source does not undo files generated in users' projects. Retain
backups and review migrations independently of Git rollback.


## Offline Aikya reference collection compositions

The nine adapted starters are documented in [Aikya reference collection SDD templates](SDD_TEMPLATES.md). They preserve the approval state machine, optional reviewed sections, canonical documentation paths, the actual-file index and the universal GENERATED BY AIKYA HARNESS footer. Empty verification and clarification reports are omitted until there is evidence or a question to record.

GENERATED BY AIKYA HARNESS
