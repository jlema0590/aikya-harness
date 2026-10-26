---
name: cicd-pipelines
description: "Secure CI/CD pipelines for lint, test, build, artifacts, release and deployment. Use for GitHub Actions and GitLab CI."
---

# CI/CD — cicd-pipelines

## Purpose
Apply a repeatable, evidence-based engineering workflow to tasks in this specialty. Use this skill when the request matches its description. Treat repository instructions and real code as the source of truth.

## Preconditions
1. Confirm task objective, scope and constraints from user context.
2. Inspect relevant files, project conventions and available tools; never invent repository structure.
3. Identify whether the task is analysis-only or permits edits. Avoid destructive or external side effects without explicit approval.
4. State material unknowns rather than manufacturing facts.

## Technical checklist
1. Inspect existing CI provider, environments, branch protections, permissions and release procedure.
2. Organize stages as validate -> test -> build -> scan -> package -> publish -> deploy with dependencies and fail-fast behavior.
3. Pin reusable actions or images to immutable revisions where feasible; apply minimum token permissions and OIDC instead of long-lived credentials.
4. Scope secrets and deployment approvals to environments; never print tokens or unmasked sensitive variables.
5. Use dependency caching based on lockfiles, avoid cross-branch cache poisoning and preserve reproducible builds.
6. Keep artifacts immutable and traceable to source revision; add rollback strategy for deployment stages.
7. Do not execute deployment, rotate secrets, create credentials or change production environments without explicit approval.

## Execution workflow
1. Inspect relevant implementation and configuration.
2. Identify risks, interfaces and smallest coherent solution.
3. Implement or review within the assigned agent permissions.
4. Run non-destructive validation available in this repository.
5. Report evidence and unresolved issues; never claim commands were run when they were not.

## Validation and deliverables
- Provide workflow stages, permissions, triggers, approval gates, artifact provenance and rollback plan.
- Validate YAML and run local/static checks if tooling is present.
- Highlight required repository secrets and settings without inventing values.

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
