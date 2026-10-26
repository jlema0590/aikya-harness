---
name: cloud-security
description: "Cloud IAM, network controls, encryption, keys, audit logging and posture review across AWS Azure GCP."
---

# Cloud security — cloud-security

## Purpose
Apply a repeatable, evidence-based engineering workflow to tasks in this specialty. Use this skill when the request matches its description. Treat repository instructions and real code as the source of truth.

## Preconditions
1. Confirm task objective, scope and constraints from user context.
2. Inspect relevant files, project conventions and available tools; never invent repository structure.
3. Identify whether the task is analysis-only or permits edits. Avoid destructive or external side effects without explicit approval.
4. State material unknowns rather than manufacturing facts.

## Technical checklist
1. Inventory identities, trust relationships, public entry points, data stores and privileged operations.
2. Review least-privilege IAM, workload identity federation, MFA for human admin and separation of duties.
3. Validate network segmentation, egress controls, private endpoints and exposure of management interfaces.
4. Review data encryption at rest/in transit, key lifecycle, backup protection and secrets management.
5. Check auditability, security monitoring, retention and response runbooks against stated requirements.
6. Do not assume a service is private solely because of its network naming; verify routes and policy intent.
7. Never disable security controls or modify live permissions without approval.

## Execution workflow
1. Inspect relevant implementation and configuration.
2. Identify risks, interfaces and smallest coherent solution.
3. Implement or review within the assigned agent permissions.
4. Run non-destructive validation available in this repository.
5. Report evidence and unresolved issues; never claim commands were run when they were not.

## Validation and deliverables
- Report findings by resource, boundary, severity, evidence and mitigation.
- Provide prioritized remediation roadmap and validation checklist.
- Separate provider-specific implementation details from portable principles.

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
