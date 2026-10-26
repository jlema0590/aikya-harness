---
name: security-audit
description: "Defensive application security audit using OWASP principles, threat models, authorization, supply chain and secrets hygiene."
---

# Application security — security-audit

## Purpose
Apply a repeatable, evidence-based engineering workflow to tasks in this specialty. Use this skill when the request matches its description. Treat repository instructions and real code as the source of truth.

## Preconditions
1. Confirm task objective, scope and constraints from user context.
2. Inspect relevant files, project conventions and available tools; never invent repository structure.
3. Identify whether the task is analysis-only or permits edits. Avoid destructive or external side effects without explicit approval.
4. State material unknowns rather than manufacturing facts.

## Technical checklist
1. Define assets, actors, trust boundaries and entry points before scanning.
2. Inspect authentication, session management, per-object authorization, multi-tenancy and least privilege.
3. Assess injection, XSS, CSRF, SSRF, insecure redirects, path traversal, deserialization and file-upload risks where applicable.
4. Review secret handling, encryption, logging, dependency risk and configuration exposures.
5. Prefer safe, non-destructive verification; never exfiltrate sensitive data or run aggressive production scans.
6. Map findings to CWE or OWASP category when reliable, but do not claim formal compliance from a code review alone.
7. Recommend mitigations aligned with existing architecture and deployment context.

## Execution workflow
1. Inspect relevant implementation and configuration.
2. Identify risks, interfaces and smallest coherent solution.
3. Implement or review within the assigned agent permissions.
4. Run non-destructive validation available in this repository.
5. Report evidence and unresolved issues; never claim commands were run when they were not.

## Validation and deliverables
- Report severity, affected asset/path, prerequisites, exploitability, impact, remediation and verification steps.
- Separate confirmed from suspected vulnerabilities and identify unavailable evidence.
- Never include secret values in reports.

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
