---
name: astro-performance
description: "Astro performance, static/server rendering, islands architecture, Tailwind, images, accessibility and SEO. Use for Astro sites."
---

# Astro + Tailwind — astro-performance

## Purpose
Apply a repeatable, evidence-based engineering workflow to tasks in this specialty. Use this skill when the request matches its description. Treat repository instructions and real code as the source of truth.

## Preconditions
1. Confirm task objective, scope and constraints from user context.
2. Inspect relevant files, project conventions and available tools; never invent repository structure.
3. Identify whether the task is analysis-only or permits edits. Avoid destructive or external side effects without explicit approval.
4. State material unknowns rather than manufacturing facts.

## Technical checklist
1. Inspect astro.config.*, integrations, rendering mode, content collections and current Tailwind version.
2. Prefer static HTML and native browser features; add an island only where interactivity justifies its JS cost.
3. Choose hydration directive intentionally: client:visible, client:idle, client:media or client:load only when warranted.
4. Optimize images with appropriate responsive formats, dimensions and load priority; avoid layout shift.
5. Use semantic structure, accessible interactions, proper heading hierarchy and keyboard support.
6. Apply design tokens and utility conventions already present; do not assume Tailwind v3 configuration in v4 projects.
7. Respect page metadata, canonical URLs, sitemap/robots and structured data where relevant.

## Execution workflow
1. Inspect relevant implementation and configuration.
2. Identify risks, interfaces and smallest coherent solution.
3. Implement or review within the assigned agent permissions.
4. Run non-destructive validation available in this repository.
5. Report evidence and unresolved issues; never claim commands were run when they were not.

## Validation and deliverables
- Identify page type, SSR/static and JS hydration decisions.
- Run astro check, build, lint and link checks if configured.
- Assess LCP, CLS, INP and total shipped JS with actual measurements where possible.

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
