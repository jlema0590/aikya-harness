---
name: testing-strategy
description: "Risk-based test strategy for frontend, backend, mobile and infrastructure changes. Use to plan or implement automated tests."
---

# Testing — testing-strategy

## Purpose
Apply a repeatable, evidence-based engineering workflow to tasks in this specialty. Use this skill when the request matches its description. Treat repository instructions and real code as the source of truth.

## Preconditions
1. Confirm task objective, scope and constraints from user context.
2. Inspect relevant files, project conventions and available tools; never invent repository structure.
3. Identify whether the task is analysis-only or permits edits. Avoid destructive or external side effects without explicit approval.
4. State material unknowns rather than manufacturing facts.

## Technical checklist
1. Inspect current tools, test commands, fixtures, CI and coverage before changing conventions.
2. Create a risk matrix of critical paths, boundary cases, failures, authorization and regressions.
3. Use unit tests for logic, integration tests for boundaries and E2E tests for user-critical journeys; avoid duplicating all scenarios across layers.
4. Prefer deterministic tests with controlled clocks and dependency seams; avoid brittle sleeps and snapshot overuse.
5. Isolate external services with contracts/test containers/fakes based on fidelity needs.
6. Do not test private implementation details when observable behavior can be asserted.
7. When adding tests, first reproduce bug or define failure, then implement minimal fix.

## Execution workflow
1. Inspect relevant implementation and configuration.
2. Identify risks, interfaces and smallest coherent solution.
3. Implement or review within the assigned agent permissions.
4. Run non-destructive validation available in this repository.
5. Report evidence and unresolved issues; never claim commands were run when they were not.

## Validation and deliverables
- Provide test matrix: scenario, level, preconditions, assertion and command.
- Execute relevant tests if allowed and record actual outcome.
- Distinguish skipped, unavailable, flaky and failed tests honestly.

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
