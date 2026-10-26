---
name: react-engineering
description: Implement and review React + TypeScript Developer projects using their
  actual versions, existing architecture, security standards, tests and build tooling.
---

# React + TypeScript Developer Engineering Skill

## Scope

Use this skill for feature work, maintenance, debugging, technical reviews and testing in React + TypeScript Developer projects. This skill covers **technology-specific implementation**, not selection of the overall software architecture.

## Operating procedure

1. Read the relevant repository files and `CLAUDE.md`; confirm actual stack, architecture, dependencies, test tooling and business context.
2. Identify the smallest scope that satisfies the request. Distinguish verified observations from hypotheses.
3. Follow the specific workflow below; prefer existing conventions unless the user explicitly requests a migration.
4. For design work, provide alternatives, a recommended default with rationale, and a staged migration plan where appropriate.
5. For implementation, write tests or update them and execute available validation; report blocked commands plainly.
6. Never imply a skill itself executed commands; tools do execution. Do not perform deployments/destructive operations without explicit authorization.

## Cross-cutting criteria

- Business correctness, explicit contracts and compatible evolution.
- Authentication/authorization at trust boundaries; input validation; secrets protected.
- Observability appropriate to runtime, meaningful logs/metrics/traces, no secrets or unnecessary PII.
- Resilience, operational cost and team maintainability proportional to system complexity.
- Tests tied to behavior; avoid testing framework internals or fragile implementation details.
- Preserve project conventions; do not add frameworks or dependencies merely because a pattern exists.


## Detect stack and constraints

- Inspect package.json; tsconfig.json; vite.config.*; next.config.*; framework/router; existing component library and test scripts.
- Confirm versions and frameworks from actual manifests rather than memory or assumptions.
- Inspect modules, entrypoints, existing DTOs, domain objects, adapters and test coverage.
- Identify configured lint/type/build/test commands before running them.

## Implementation standards
- Default to function components and typed props; prefer derived values over duplicated state.
- Use effects for synchronization with external systems, not routine derived state; obey hook rules.
- Follow existing router/server rendering model, distinguishing RSC/server code from browser-only components when relevant.
- Use semantic elements, focus management, accessible form fields and loading/error/empty states.
- Avoid premature memoization and global state; profile measured bottlenecks.

## Choose architecture independently

- **Clean Architecture:** domain/use-case code independent of frameworks; check dependency direction. Invoke `/clean-architecture` if available and relevant.
- **Monolith:** cohesive modules in one deployment, clear module boundaries; `/modular-monolith-architecture`.
- **Layered:** presentation/service/persistence responsibilities and clean interfaces; `/layered-architecture`.
- **Microservices:** explicit service ownership, independent deployment and data boundaries; `/microservices-architecture`.
- **Event-driven:** durable event contracts, idempotency and eventual consistency; `/event-driven-architecture`.

Apply only the architecture selected or already present. Multiple architectural styles may coexist at different scopes (for example Clean Architecture within a modular monolith).

## Test strategy
- React Testing Library/Vitest/Jest as configured; verify user-visible behavior and accessibility.
- Check hydration, async error boundaries, network states and data freshness when applicable.

## Validation commands (select only configured tools)
- `npm run lint / pnpm lint / yarn lint (match scripts)`
- `npm run test / npm run build (configured equivalents)`

## Review before completion

- No unrelated refactors; no direct secrets or credentials; no accidental destructive migrations.
- Business logic and API contracts remain compatible unless changes are approved.
- Accessibility (frontends), authorization (backends), errors and empty states addressed where relevant.
- Tests actually run with outcomes and limitations described, including failures not caused by this change.

## Report format

1. **Context/versions**: framework and tools actually detected.
2. **Change summary**: behavior, files and architecture decisions.
3. **Checks**: exact commands run, pass/fail status and gaps.
4. **Risks and next actions**: migration, compatibility and rollout considerations.

## Official references
- https://react.dev/learn/thinking-in-react
- https://react.dev/reference/react
