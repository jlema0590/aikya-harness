---
name: vue-architecture
description: "Vue 3 TypeScript Composition API feature architecture, Pinia, routing, components and composables. Use for Vue frontend design."
---

# Vue 3 — vue-architecture

## Purpose
Apply a repeatable, evidence-based engineering workflow to tasks in this specialty. Use this skill when the request matches its description. Treat repository instructions and real code as the source of truth.

## Preconditions
1. Confirm task objective, scope and constraints from user context.
2. Inspect relevant files, project conventions and available tools; never invent repository structure.
3. Identify whether the task is analysis-only or permits edits. Avoid destructive or external side effects without explicit approval.
4. State material unknowns rather than manufacturing facts.

## Technical checklist
1. Inspect package.json and determine Vue/Vite/Nuxt, state, routing, SSR and styling conventions.
2. Prefer script setup with TypeScript only when consistent with project conventions.
3. Separate page orchestration, feature components, composables, service/API layer and shared UI components.
4. Scope state locally; use Pinia for genuine shared state and keep server cache strategy explicit.
5. Use typed props/emits; avoid mutating props, unstable v-for keys and excessive watchers.
6. Handle loading, empty, error, permission, optimistic updates and cancellation.
7. Respect accessibility, keyboard operation, semantic HTML, focus and responsive layout.

## Execution workflow
1. Inspect relevant implementation and configuration.
2. Identify risks, interfaces and smallest coherent solution.
3. Implement or review within the assigned agent permissions.
4. Run non-destructive validation available in this repository.
5. Report evidence and unresolved issues; never claim commands were run when they were not.

## Validation and deliverables
- Document component boundaries, data flow and state ownership.
- Run vue-tsc, lint, Vitest, build or equivalent available commands.
- Test user-facing behavior, routing guards and edge states.

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
