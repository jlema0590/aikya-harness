---
name: node-api-design
description: "Node.js TypeScript backend API design including contracts, authentication, validation, persistence and observability. Use for services and APIs."
---

# Node.js / TypeScript APIs — node-api-design

## Purpose
Apply a repeatable, evidence-based engineering workflow to tasks in this specialty. Use this skill when the request matches its description. Treat repository instructions and real code as the source of truth.

## Preconditions
1. Confirm task objective, scope and constraints from user context.
2. Inspect relevant files, project conventions and available tools; never invent repository structure.
3. Identify whether the task is analysis-only or permits edits. Avoid destructive or external side effects without explicit approval.
4. State material unknowns rather than manufacturing facts.

## Technical checklist
1. Inspect package.json, framework, folder conventions, tsconfig, schema validation, auth and database access.
2. Design resource and endpoint contracts first: method/path, request schema, response schema, errors, pagination, idempotency and versioning.
3. Validate external input at trust boundaries; map errors to stable non-leaking responses.
4. Enforce authorization per resource and tenant; authenticated does not mean authorized.
5. Keep handlers thin, domain logic independent of transport and persistence behind cohesive abstractions.
6. Use transactions for atomic writes, parameterized queries and explicit migration/rollback plans.
7. Define timeouts, retries with backoff, idempotency and observability for integrations and async jobs.

## Execution workflow
1. Inspect relevant implementation and configuration.
2. Identify risks, interfaces and smallest coherent solution.
3. Implement or review within the assigned agent permissions.
4. Run non-destructive validation available in this repository.
5. Report evidence and unresolved issues; never claim commands were run when they were not.

## Validation and deliverables
- Provide an endpoint contract table and OpenAPI changes when applicable.
- Run project lint/typecheck/tests; cover 2xx, 4xx, 5xx and auth cases.
- Call out compatibility impacts, migrations and unsafe defaults.

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
