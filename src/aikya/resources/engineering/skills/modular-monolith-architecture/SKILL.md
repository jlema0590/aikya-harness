---
name: modular-monolith-architecture
description: Apply Monolithic / Modular Monolith to design/review software boundaries,
  trade-offs and incremental migration. Use for architecture decisions, technical
  plans and refactors.
---

# Monolithic / Modular Monolith Skill

## Purpose and selection criteria

Preserve operational simplicity of one deployment while maintaining cohesive modules and explicit boundaries.

Use this skill when analyzing or designing monolithic / modular monolith. It is language-agnostic. Pair it with a relevant language engineering skill when implementation is requested. Do **not** automatically convert a working project to this style.

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
- Identify deployment units, code modules, schemas, cross-module imports and ownership.
- Check whether module boundaries reflect capabilities instead of controller/repository silos.
- Inspect build, deployment, data transactions, startup dependencies and change frequency.

## Design workflow
1. Decide whether a simple monolith or modular monolith is justified by scale and team needs.
2. Define bounded capabilities, public module APIs, internal implementation and dependency rules.
3. Allow in-process synchronous calls where suitable; use internal events only if valuable.
4. Keep transaction handling simple; document when transactions cross modules.
5. Design seams that make later extraction possible without committing to distributed systems.

## Architecture decision record (ADR) template

- **Context / business drivers:** team size, use cases, availability/latency, domain complexity, deployment and delivery constraints.
- **Decision:** the architecture and boundaries proposed; which parts will remain unchanged.
- **Alternatives:** at least one simpler option, one rejected option and reasons.
- **Dependency/data flow:** show a concise textual diagram and permitted/forbidden dependencies.
- **Consequences:** testing, development velocity, performance, scaling, deployment, security, cost and operational complexity.
- **Migration:** ordered, reversible steps with intermediate checks.
- **Validation:** measurable acceptance checks and responsibilities.

## Anti-patterns to flag
- Do not treat “monolith” as an anti-pattern.
- Do not introduce message brokers, service mesh or per-module databases by default.
- Avoid a shared common module that silently couples every feature.

## Verification strategy
- Architecture/dependency tests for module visibility.
- Feature-focused integration tests against one deployable application.
- Operational checks for startup, migration and deployment.

## Handoff format

Return a decision + bounded implementation backlog suitable for `planner` and the chosen developer (Java/.NET/Python/React/Angular/Kotlin). Include an impact matrix by file/module where observed, contract changes, dependencies, data implications and a rollback plan. If the architecture does not fit, say why and propose the simpler option.

## Official references
- https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures
