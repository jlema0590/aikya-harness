---
name: event-driven-architecture
description: Apply Event-Driven Architecture to design/review software boundaries,
  trade-offs and incremental migration. Use for architecture decisions, technical
  plans and refactors.
---

# Event-Driven Architecture Skill

## Purpose and selection criteria

Make temporal decoupling explicit: contracts, eventual consistency, delivery guarantees, replay, idempotency, observability and recovery.

Use this skill when analyzing or designing event-driven architecture. It is language-agnostic. Pair it with a relevant language engineering skill when implementation is requested. Do **not** automatically convert a working project to this style.

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
- Identify producers, consumers, event taxonomy, broker, ordering needs, retention and schemas.
- Trace transactional boundaries for dual writes, event versioning and ownership.
- Check retries, poison messages, DLQs, correlation, replays and PII in payloads.

## Design workflow
1. Differentiate commands from domain events and integration events with past-tense names.
2. Define schema, required metadata, keys, versioning, consumer responsibilities and PII policies.
3. Select broker/queue/stream based on throughput, ordering, retention and replay requirements.
4. Mitigate dual-write using transactional outbox or equivalent where required.
5. Design at-least-once-safe handlers; use deduplication and idempotency and document consistency.

## Architecture decision record (ADR) template

- **Context / business drivers:** team size, use cases, availability/latency, domain complexity, deployment and delivery constraints.
- **Decision:** the architecture and boundaries proposed; which parts will remain unchanged.
- **Alternatives:** at least one simpler option, one rejected option and reasons.
- **Dependency/data flow:** show a concise textual diagram and permitted/forbidden dependencies.
- **Consequences:** testing, development velocity, performance, scaling, deployment, security, cost and operational complexity.
- **Migration:** ordered, reversible steps with intermediate checks.
- **Validation:** measurable acceptance checks and responsibilities.

## Anti-patterns to flag
- Never promise exactly-once end-to-end business effect without a proof and exact scope.
- Do not publish large sensitive aggregates without need.
- Avoid a broker when a direct call is simpler and meets requirements.

## Verification strategy
- Schema compatibility and producer/consumer contract tests.
- Duplicate delivery, out-of-order, retry, DLQ and replay simulations.
- Metrics for lag, redelivery, failures and event-to-business outcome latency.

## Handoff format

Return a decision + bounded implementation backlog suitable for `planner` and the chosen developer (Java/.NET/Python/React/Angular/Kotlin). Include an impact matrix by file/module where observed, contract changes, dependencies, data implications and a rollback plan. If the architecture does not fit, say why and propose the simpler option.

## Official references
- https://cloudevents.io/
