---
name: code-review
description: "Evidence-based code review focused on correctness, maintainability, architecture and regressions. Use when assessing diffs or pull requests."
---

# Code review — code-review

## Purpose
Apply a repeatable, evidence-based engineering workflow to tasks in this specialty. Use this skill when the request matches its description. Treat repository instructions and real code as the source of truth.

## Preconditions
1. Confirm task objective, scope and constraints from user context.
2. Inspect relevant files, project conventions and available tools; never invent repository structure.
3. Identify whether the task is analysis-only or permits edits. Avoid destructive or external side effects without explicit approval.
4. State material unknowns rather than manufacturing facts.

## Technical checklist
1. Define review scope and inspect diff, nearby call sites, public contracts and tests.
2. Prioritize actionable defects over style opinions; avoid speculative findings with no evidence.
3. Check functionality, edge cases, concurrency, error paths, type safety, compatibility and performance.
4. Review auth boundaries, secrets and data exposure; route serious security findings to security-audit.
5. Respect repository conventions; suggest redesign only when a verified issue warrants it.
6. Distinguish blockers from medium- and low-severity opportunities.

## Execution workflow
1. Inspect relevant implementation and configuration.
2. Identify risks, interfaces and smallest coherent solution.
3. Implement or review within the assigned agent permissions.
4. Run non-destructive validation available in this repository.
5. Report evidence and unresolved issues; never claim commands were run when they were not.

## Validation and deliverables
- Report each finding with severity, file and line, exact impact, reproduction path and concrete fix.
- Explicitly state what was not reviewed or tested.
- If no confirmed findings, state that and mention residual risks; do not manufacture issues.

## Output format
- **Scope:** examined components and context.
- **Decisions:** rationale, trade-offs and assumptions.
- **Changes/Findings:** concrete files/resources, prioritized where relevant.
- **Verification:** exact commands/checks performed and results, or reason not performed.
- **Risks and next actions:** remaining work with accountable action.

## Guardrails
- Respect higher-priority user/project/security instructions and tool permissions.
- Do not introduce unrequested frameworks or sweeping refactors.
- Never expose secrets or claim security/compliance certification without evidence.
- Do not make production changes without explicit authorization.
- Reply in Spanish by default unless the user requests another language.
