---
name: cloud-architecture
description: "Provider-aware cloud architecture assessment emphasizing reliability, security, operations, performance and cost. Use for AWS, Azure or GCP design."
---

# Cloud architecture — cloud-architecture

## Purpose
Apply a repeatable, evidence-based engineering workflow to tasks in this specialty. Use this skill when the request matches its description. Treat repository instructions and real code as the source of truth.

## Preconditions
1. Confirm task objective, scope and constraints from user context.
2. Inspect relevant files, project conventions and available tools; never invent repository structure.
3. Identify whether the task is analysis-only or permits edits. Avoid destructive or external side effects without explicit approval.
4. State material unknowns rather than manufacturing facts.

## Technical checklist
1. Discover provider, region, workloads, business SLOs, RTO/RPO, regulatory boundaries and existing landing zone.
2. Start with context diagram, trust boundaries, data classification and dependency map.
3. Compare options by reliability, security, operational complexity, latency, cost and vendor lock-in.
4. Plan IAM, network segmentation, secrets, logging, backup, recovery, service quotas and multi-AZ/region only where justified.
5. Apply provider Well-Architected principles without asserting compliance certification.
6. Prefer Infrastructure as Code, isolated environments and staged rollout with rollback strategy.
7. Make assumptions and unknowns explicit rather than inventing provider prices or SLAs.

## Execution workflow
1. Inspect relevant implementation and configuration.
2. Identify risks, interfaces and smallest coherent solution.
3. Implement or review within the assigned agent permissions.
4. Run non-destructive validation available in this repository.
5. Report evidence and unresolved issues; never claim commands were run when they were not.

## Validation and deliverables
- Deliver diagrams in Mermaid when useful, ADR, risks and migration/rollback phases.
- Define measurable SLOs, failure testing and cost estimation inputs.
- Flag decisions needing stakeholder approval.

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
