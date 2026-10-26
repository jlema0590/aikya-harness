---
name: terraform-iac
description: "Terraform or OpenTofu infrastructure-as-code patterns, modules, state, plans and safe changes. Use for IaC development and review."
---

# Terraform/OpenTofu — terraform-iac

## Purpose
Apply a repeatable, evidence-based engineering workflow to tasks in this specialty. Use this skill when the request matches its description. Treat repository instructions and real code as the source of truth.

## Preconditions
1. Confirm task objective, scope and constraints from user context.
2. Inspect relevant files, project conventions and available tools; never invent repository structure.
3. Identify whether the task is analysis-only or permits edits. Avoid destructive or external side effects without explicit approval.
4. State material unknowns rather than manufacturing facts.

## Technical checklist
1. Inspect versions, providers, modules, workspace/environment strategy, state backend and lockfiles.
2. Prefer reusable but cohesive modules; expose minimal typed variables with validation and clear outputs.
3. Pin provider/module versions appropriately and document upgrade policy.
4. Protect remote state with access controls, encryption, locking and separate environments; state may contain secrets.
5. Never execute apply, destroy, state rm/mv, import, force-unlock or production changes without explicit approval.
6. Review plans for replacements, resource drift, privilege escalation, public exposure and unexpected cost changes.
7. Use policy-as-code/security checks already adopted by the project.

## Execution workflow
1. Inspect relevant implementation and configuration.
2. Identify risks, interfaces and smallest coherent solution.
3. Implement or review within the assigned agent permissions.
4. Run non-destructive validation available in this repository.
5. Report evidence and unresolved issues; never claim commands were run when they were not.

## Validation and deliverables
- Run fmt -check, validate and plan only where credentials, approval and environment support it.
- Summarize add/change/destroy and sensitive impacts from actual plans.
- Provide rollback/recovery and state backup considerations.

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
