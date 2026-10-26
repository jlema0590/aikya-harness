---
name: flutter-architecture
description: "Flutter and Dart application architecture, state management, navigation, dependency injection and testing. Use when designing or changing Flutter features."
---

# Flutter/Dart — flutter-architecture

## Purpose
Apply a repeatable, evidence-based engineering workflow to tasks in this specialty. Use this skill when the request matches its description. Treat repository instructions and real code as the source of truth.

## Preconditions
1. Confirm task objective, scope and constraints from user context.
2. Inspect relevant files, project conventions and available tools; never invent repository structure.
3. Identify whether the task is analysis-only or permits edits. Avoid destructive or external side effects without explicit approval.
4. State material unknowns rather than manufacturing facts.

## Technical checklist
1. Inspect pubspec.yaml, lib/, test/, router, dependency injection and current state library before recommending changes.
2. Respect existing Riverpod, BLoC, Provider or other state management; never silently introduce a competing framework.
3. Separate presentation/widgets, application state/use cases, domain contracts and data repositories where project complexity warrants it.
4. Model loading, empty, error, success and retry states; handle cancellation/disposal and lifecycle safely.
5. Use typed immutable models, null safety, explicit errors and consistent serialization.
6. Ensure responsive layout, accessibility semantics, localization, app lifecycle and platform support.
7. Never embed long-lived secrets in mobile binaries; use secure storage for sensitive local data when appropriate.

## Execution workflow
1. Inspect relevant implementation and configuration.
2. Identify risks, interfaces and smallest coherent solution.
3. Implement or review within the assigned agent permissions.
4. Run non-destructive validation available in this repository.
5. Report evidence and unresolved issues; never claim commands were run when they were not.

## Validation and deliverables
- Document feature boundaries and dependency direction.
- Verify dart format, flutter analyze and relevant flutter test commands when available.
- List widget and integration tests for new behavior and test state transitions.

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
