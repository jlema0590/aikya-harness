---
name: layered-architecture
description: Apply Layered / N-tier Architecture to design/review software boundaries,
  trade-offs and incremental migration. Use for architecture decisions, technical
  plans and refactors.
---

# Layered / N-tier Architecture Skill

## Purpose and selection criteria

Use clear and testable layer contracts while avoiding incidental coupling and excessive pass-through layers.

Use this skill when analyzing or designing layered / n-tier architecture. It is language-agnostic. Pair it with a relevant language engineering skill when implementation is requested. Do **not** automatically convert a working project to this style.

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
- Map presentation/API, application/service, domain/business and persistence/infrastructure responsibilities.
- Trace calls and imports for layer skipping, cyclic dependencies and duplicate validation.
- Inspect DTO/entity boundaries, security, transaction handling and exception mappings.

## Design workflow
1. Choose a minimal layer set aligned with existing conventions; separate physical tiers only when needed.
2. Document allowed dependencies and request/response data flow.
3. Assign business logic, validation, authorization and transaction ownership explicitly.
4. Introduce reusable interfaces only for meaningful boundaries or testing seams.
5. Prefer feature folders within layers if this improves discoverability.

## Architecture decision record (ADR) template

- **Context / business drivers:** team size, use cases, availability/latency, domain complexity, deployment and delivery constraints.
- **Decision:** the architecture and boundaries proposed; which parts will remain unchanged.
- **Alternatives:** at least one simpler option, one rejected option and reasons.
- **Dependency/data flow:** show a concise textual diagram and permitted/forbidden dependencies.
- **Consequences:** testing, development velocity, performance, scaling, deployment, security, cost and operational complexity.
- **Migration:** ordered, reversible steps with intermediate checks.
- **Validation:** measurable acceptance checks and responsibilities.

## Anti-patterns to flag
- Do not confuse logical layers with physical deployment tiers.
- Avoid anemic pass-through services that add no value.
- Avoid returning persistence entities directly across public API boundaries.

## Verification strategy
- Unit tests for business services and validation.
- Integration tests for data access and HTTP endpoints.
- Static checks for cyclic or forbidden dependencies.

## Handoff format

Return a decision + bounded implementation backlog suitable for `planner` and the chosen developer (Java/.NET/Python/React/Angular/Kotlin). Include an impact matrix by file/module where observed, contract changes, dependencies, data implications and a rollback plan. If the architecture does not fit, say why and propose the simpler option.

## Official references
- https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures
