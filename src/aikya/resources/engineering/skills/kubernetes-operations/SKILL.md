---
name: kubernetes-operations
description: "Kubernetes manifests, Helm, workloads, RBAC, networking, rollout and troubleshooting. Use for K8s platform operations."
---

# Kubernetes — kubernetes-operations

## Purpose
Apply a repeatable, evidence-based engineering workflow to tasks in this specialty. Use this skill when the request matches its description. Treat repository instructions and real code as the source of truth.

## Preconditions
1. Confirm task objective, scope and constraints from user context.
2. Inspect relevant files, project conventions and available tools; never invent repository structure.
3. Identify whether the task is analysis-only or permits edits. Avoid destructive or external side effects without explicit approval.
4. State material unknowns rather than manufacturing facts.

## Technical checklist
1. Inspect cluster version, deployment method, namespaces, policies, controllers and current workloads.
2. Specify requests/limits, startup/readiness/liveness probes, rollout strategy and disruption budget based on workload.
3. Minimize RBAC, enforce appropriate NetworkPolicies and Pod security constraints; avoid privileged containers.
4. Handle secrets using approved management pattern; never print or commit secret data.
5. Account for autoscaling, DNS, ingress, storage, disruption and graceful shutdown.
6. Do not kubectl apply/delete, helm upgrade/install/uninstall or modify a live cluster without explicit approval.
7. Prefer dry-run/schema checks and observable rollout verification.

## Execution workflow
1. Inspect relevant implementation and configuration.
2. Identify risks, interfaces and smallest coherent solution.
3. Implement or review within the assigned agent permissions.
4. Run non-destructive validation available in this repository.
5. Report evidence and unresolved issues; never claim commands were run when they were not.

## Validation and deliverables
- Provide manifests/chart diff, target namespace, expected changes and rollback commands.
- Validate rendered Helm templates and schema where tooling exists.
- Explain monitoring signals and failure modes for rollout.

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
