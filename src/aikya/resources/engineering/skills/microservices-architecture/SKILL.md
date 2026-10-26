---
name: microservices-architecture
description: Apply Microservices Architecture to design/review software boundaries,
  trade-offs and incremental migration. Use for architecture decisions, technical
  plans and refactors.
---

# Microservices Architecture Skill

## Purpose and selection criteria

Justify independently deployable services using bounded contexts, team autonomy and operational capability; favor modular monolith when costs exceed benefits.

Use this skill when analyzing or designing microservices architecture. It is language-agnostic. Pair it with a relevant language engineering skill when implementation is requested. Do **not** automatically convert a working project to this style.

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
- Inventory services, dependencies, deploy cadence, domain capabilities, data stores and shared libraries.
- Trace synchronous call chains, service-to-service authentication, topology and failure modes.
- Inspect monitoring, tracing, SLOs, CI/CD, secrets and operational ownership.

## Design workflow
1. Define bounded contexts and ownership using business capabilities, not arbitrary technical slices.
2. Clarify per-service data ownership, consistency requirements and cross-service queries.
3. Specify API contracts, event schemas, compatibility policy and versioning.
4. Design timeouts, retries, backoff, circuit breakers, idempotency and failure isolation.
5. Plan observability, cost, release strategy, local development and incremental extraction.

## Architecture decision record (ADR) template

- **Context / business drivers:** team size, use cases, availability/latency, domain complexity, deployment and delivery constraints.
- **Decision:** the architecture and boundaries proposed; which parts will remain unchanged.
- **Alternatives:** at least one simpler option, one rejected option and reasons.
- **Dependency/data flow:** show a concise textual diagram and permitted/forbidden dependencies.
- **Consequences:** testing, development velocity, performance, scaling, deployment, security, cost and operational complexity.
- **Migration:** ordered, reversible steps with intermediate checks.
- **Validation:** measurable acceptance checks and responsibilities.

## Anti-patterns to flag
- No microservices solely “for scalability” without evidence.
- Avoid shared writable databases and chatty synchronous chains.
- Avoid claiming exactly-once delivery or distributed transactions are trivial.

## Verification strategy
- Contract tests across service boundaries.
- Failure injection tests for dependency outages, retries, DLQs and timeouts.
- Trace correlation, SLOs, deploy independence and operational runbooks.

## Handoff format

Return a decision + bounded implementation backlog suitable for `planner` and the chosen developer (Java/.NET/Python/React/Angular/Kotlin). Include an impact matrix by file/module where observed, contract changes, dependencies, data implications and a rollback plan. If the architecture does not fit, say why and propose the simpler option.

## Official references
- https://learn.microsoft.com/en-us/dotnet/architecture/microservices/architect-microservice-container-applications/microservices-architecture
