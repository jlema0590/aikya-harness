---
name: clean-architecture
description: Apply Clean Architecture to design/review software boundaries, trade-offs
  and incremental migration. Use for architecture decisions, technical plans and refactors.
---

# Clean Architecture Skill

## Purpose and selection criteria

Domain/application rules remain independent of infrastructure, persistence, HTTP, frameworks and delivery mechanisms.

Use this skill when analyzing or designing clean architecture. It is language-agnostic. Pair it with a relevant language engineering skill when implementation is requested. Do **not** automatically convert a working project to this style.

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


## Discovery checklist
- Identify existing domain entities, use cases, application services, ports and adapters.
- Trace dependencies and imports; identify dependencies that point from domain inward/outward incorrectly.
- Inspect DTO mapping, transaction ownership, dependency-injection composition root and tests.

## Design workflow
1. Define business capabilities and use cases before choosing folder names.
2. Separate domain rules from application orchestration, interfaces and adapters; use interfaces only at useful boundaries.
3. Place implementations in infrastructure; wire dependencies at the composition root.
4. Keep framework-specific validation, controllers and ORM entities outside domain objects when practical.
5. Propose an incremental migration plan with no large-bang rewrite.

## Architecture decision record (ADR) template

- **Context / business drivers:** team size, use cases, availability/latency, domain complexity, deployment and delivery constraints.
- **Decision:** the architecture and boundaries proposed; which parts will remain unchanged.
- **Alternatives:** at least one simpler option, one rejected option and reasons.
- **Dependency/data flow:** show a concise textual diagram and permitted/forbidden dependencies.
- **Consequences:** testing, development velocity, performance, scaling, deployment, security, cost and operational complexity.
- **Migration:** ordered, reversible steps with intermediate checks.
- **Validation:** measurable acceptance checks and responsibilities.

## Anti-patterns to flag
- Do not create an interface for every class or a new layer for every function.
- Do not force DDD aggregates or CQRS on simple CRUD.
- Avoid leaking ORM/query/web request types into core business abstractions.

## Verification strategy
- Dependency-rule verification by inspection/static architecture tests.
- Unit tests for use cases without database or web framework.
- Integration tests for repositories, transactions and adapters.

## Handoff format

Return a decision + bounded implementation backlog suitable for `planner` and the chosen developer (Java/.NET/Python/React/Angular/Kotlin). Include an impact matrix by file/module where observed, contract changes, dependencies, data implications and a rollback plan. If the architecture does not fit, say why and propose the simpler option.

## Official references
- https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures
