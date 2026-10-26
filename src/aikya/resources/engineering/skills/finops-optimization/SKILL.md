---
name: finops-optimization
description: "Cloud cost management, unit economics, tagging, rightsizing, commitments and budgeting. Use for FinOps decisions."
---

# Cloud FinOps — finops-optimization

## Purpose
Apply a repeatable, evidence-based engineering workflow to tasks in this specialty. Use this skill when the request matches its description. Treat repository instructions and real code as the source of truth.

## Preconditions
1. Confirm task objective, scope and constraints from user context.
2. Inspect relevant files, project conventions and available tools; never invent repository structure.
3. Identify whether the task is analysis-only or permits edits. Avoid destructive or external side effects without explicit approval.
4. State material unknowns rather than manufacturing facts.

## Technical checklist
1. Establish provider, billing scope, timeframe, currency, regions, traffic and cost allocation dimensions.
2. Use real billing/export data whenever provided; label estimates and assumptions when actuals are absent.
3. Attribute costs by workload, owner, environment and business unit; identify unallocated spend.
4. Analyze compute utilization, storage tiering, data transfer, managed-service idle capacity and autoscaling.
5. Consider reservations/savings plans/commitments only with demand stability and lock-in risk quantified.
6. Compare optimization options against SLOs, availability, performance and engineering effort.
7. Do not invent current provider prices; require verification for financial decisions.

## Execution workflow
1. Inspect relevant implementation and configuration.
2. Identify risks, interfaces and smallest coherent solution.
3. Implement or review within the assigned agent permissions.
4. Run non-destructive validation available in this repository.
5. Report evidence and unresolved issues; never claim commands were run when they were not.

## Validation and deliverables
- Provide baseline, opportunity, expected monthly savings range, confidence, implementation risk and owner.
- Define monitoring KPIs: spend, forecast variance, coverage/utilization and unit cost.
- Distinguish quick wins from changes needing load testing and approval.

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
