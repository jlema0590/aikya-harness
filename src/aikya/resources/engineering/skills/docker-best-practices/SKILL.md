---
name: docker-best-practices
description: "Secure and efficient Dockerfiles, Compose and container runtime configuration. Use for containerizing and hardening services."
---

# Docker — docker-best-practices

## Purpose
Apply a repeatable, evidence-based engineering workflow to tasks in this specialty. Use this skill when the request matches its description. Treat repository instructions and real code as the source of truth.

## Preconditions
1. Confirm task objective, scope and constraints from user context.
2. Inspect relevant files, project conventions and available tools; never invent repository structure.
3. Identify whether the task is analysis-only or permits edits. Avoid destructive or external side effects without explicit approval.
4. State material unknowns rather than manufacturing facts.

## Technical checklist
1. Inspect application build, lockfile, runtime versions, ports and existing Dockerfiles before editing.
2. Prefer multi-stage builds, pinned supported base image versions and minimal runtime dependencies.
3. Use non-root execution, least permissions, read-only filesystem when feasible and explicit health checks.
4. Order layers for cache efficiency; protect build context with .dockerignore and avoid copying secrets.
5. Use BuildKit secrets for build credentials; never use ARG/ENV for secrets that persist in images.
6. In Compose, separate dev and production concerns, set bounded restart policies and named volumes consciously.
7. Consider architecture/platform compatibility, signal handling, startup/shutdown and graceful termination.

## Execution workflow
1. Inspect relevant implementation and configuration.
2. Identify risks, interfaces and smallest coherent solution.
3. Implement or review within the assigned agent permissions.
4. Run non-destructive validation available in this repository.
5. Report evidence and unresolved issues; never claim commands were run when they were not.

## Validation and deliverables
- Produce Dockerfile/Compose change rationale and build commands.
- Validate docker build/config where Docker is available, and scan images if project tooling exists.
- Record image size, user, ports, health check and residual risks if measured.

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
