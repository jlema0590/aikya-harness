---
name: angular-engineering
description: Implement and review Angular + TypeScript Developer projects using their
  actual versions, existing architecture, security standards, tests and build tooling.
---

# Angular + TypeScript Developer Engineering Skill

## Scope

Use this skill for feature work, maintenance, debugging, technical reviews and testing in Angular + TypeScript Developer projects. This skill covers **technology-specific implementation**, not selection of the overall software architecture.

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

- Inspect angular.json; package.json; tsconfig.app.json; src/app; Angular version; control-flow/template conventions.
- Confirm versions and frameworks from actual manifests rather than memory or assumptions.
- Inspect modules, entrypoints, existing DTOs, domain objects, adapters and test coverage.
- Identify configured lint/type/build/test commands before running them.

## Implementation standards
- Follow installed Angular version, standalone defaults where applicable, and existing project architecture.
- Use signals/computed for local derived state when aligned with the codebase; use RxJS for streams and cancellation where appropriate.
- Keep templates readable and types explicit; do not add effects for simple data derivation.
- Scope providers and services intentionally; use interceptors and route guards for their appropriate concerns, not as the sole authorization gate.
- Prefer OnPush-compatible immutable flows, track keys in loops and accessible HTML.

## Choose architecture independently

- **Clean Architecture:** domain/use-case code independent of frameworks; check dependency direction. Invoke `/clean-architecture` if available and relevant.
- **Monolith:** cohesive modules in one deployment, clear module boundaries; `/modular-monolith-architecture`.
- **Layered:** presentation/service/persistence responsibilities and clean interfaces; `/layered-architecture`.
- **Microservices:** explicit service ownership, independent deployment and data boundaries; `/microservices-architecture`.
- **Event-driven:** durable event contracts, idempotency and eventual consistency; `/event-driven-architecture`.

Apply only the architecture selected or already present. Multiple architectural styles may coexist at different scopes (for example Clean Architecture within a modular monolith).

## Test strategy
- Angular TestBed and existing runner; test components/services, router guards, interceptors and accessibility.
- Validate production build, AOT/strict template checks and subscription cleanup.

## Validation commands (select only configured tools)
- `npx ng test (if configured)`
- `npx ng build (if configured)`

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
- https://angular.dev/style-guide
- https://angular.dev/guide/signals
