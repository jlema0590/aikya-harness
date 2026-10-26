---
name: nextjs-architecture
description: >
  Engineering playbook for Next.js projects with TypeScript, Tailwind CSS and
  shadcn/ui. Use when building or reviewing App Router features, server/client
  boundaries, data mutations, design systems, forms, security, tests and performance.
---

# Next.js Architecture — TypeScript + Tailwind CSS + shadcn/ui

## Scope and preflight

1. Read `package.json` and lockfile. Identify Next.js/React/Tailwind versions and package manager.
2. Check App Router (`app/`, `src/app/`) versus Pages Router; respect existing choice.
3. Read `tsconfig.json`, `next.config.*`, `components.json`, `postcss.config.*`, global CSS, aliases and reusable UI.
4. Identify runtime, authentication, data fetching, tests, CI and deployment conventions.
5. Do not install packages or run component generators unless needed for the task. Explain meaningful new dependencies.

## Recommended responsibility boundaries

- **Route segments (`app/`)**: route-specific UI, metadata, `loading`, `error`, `not-found`, layout composition.
- **Server Components**: server-side read access and composition; never expose secrets to client components.
- **Client Components**: local interactivity, events, browser APIs and client-only libraries. Add `use client` at the smallest practical subtree.
- **Server mutations**: validate input, recheck authentication and authorization, persist changes transactionally as needed, invalidate affected data according to installed framework behavior.
- **Route Handlers**: external/webhook/API entrypoints, with input validation and appropriate HTTP responses; validate webhook signatures when applicable.
- **Feature folders**: co-locate feature-oriented components, schemas, actions, tests and hooks when repository conventions allow. Do not force an architecture migration.

Example structure (illustrative, not mandatory):

```text
src/
  app/
    (dashboard)/tasks/page.tsx
    (dashboard)/tasks/loading.tsx
    (dashboard)/tasks/error.tsx
  features/tasks/
    components/task-form.tsx
    components/task-list.tsx
    actions.ts
    schemas.ts
    queries.ts
  components/ui/
  lib/
```

## TypeScript and data correctness

- Prefer strict TypeScript and explicit domain/request/response types.
- Validate untrusted payloads at runtime (reuse existing schema validator such as Zod if installed).
- Do not confuse compile-time types with server-side validation.
- Implement predictable error paths and user-friendly feedback; avoid leaking internal error details.

## Tailwind CSS and shadcn/ui

1. Inspect `components.json`; it defines aliases, component settings and theming for the CLI.
2. Inspect existing `src/components/ui` or configured UI path. Reuse available primitives.
3. Compose primitives for feature-specific components; keep base components stable unless customization is intentional.
4. Use design tokens/CSS variables and semantic classes; preserve dark mode.
5. In Tailwind v4 prefer the CSS-first approach already used by the repository; in v3 honor existing `tailwind.config.*`. Never copy configuration across major versions blindly.
6. Include hover/focus/disabled/loading/empty/error states and keyboard accessibility.
7. For forms, use accessible labels, inline validation messages, server verification and clear pending feedback. Use installed form libraries when present; do not add one by default.
8. Before running `shadcn add`, check whether component exists; use the project's package manager and review generated code/diffs.

## Rendering, fetching and caching

- Prefer static/server delivery when possible; use client hydration only where interaction needs it.
- Prevent N+1 requests and avoid sequential independent reads.
- Check installed Next.js version before applying `fetch` caching defaults, `revalidatePath`, `revalidateTag`, async route props and other version-sensitive APIs.
- Use metadata APIs, `next/image`, `next/font`, streaming/Suspense appropriately where supported.
- Keep sensitive API keys out of browser-visible code and responses.

## Security checklist

- Authentication and authorization are separate; check object-level access per mutation or resource.
- Verify permissions in every Server Action and Route Handler, not only in the UI or middleware.
- Validate redirects, uploads, external URLs and input size.
- Review session/cookie policies, CSRF for relevant entrypoints and sensitive data logging.
- Use rate limits for abuse-sensitive endpoints if supported by the architecture.

## Testing and verification

- Define behavioral acceptance criteria before coding.
- Unit tests for pure logic; component tests for interactions; integration tests for server behaviors; E2E for critical journeys.
- Validate mobile and desktop, keyboard navigation and screen-reader labels.
- Run only scripts actually defined in `package.json` (e.g. `lint`, `typecheck`, `test`, `build`). Use the lockfile's package manager.
- Record which checks ran, failed, or were unavailable. Do not infer success from missing errors in an unexecuted command.

## Output contract

Return in Spanish:

1. **Diagnóstico**: versions, router, stack, important repository conventions.
2. **Decisiones**: server/client boundaries, data validation, component reuse.
3. **Implementación**: changed files and behavior.
4. **Accesibilidad y seguridad**: verified considerations.
5. **Validación**: executed commands with real outcomes.
6. **Riesgos pendientes**: explicit uncertainties or manual checks.

## Official references

- https://nextjs.org/docs/app
- https://nextjs.org/docs/app/getting-started/server-and-client-components
- https://ui.shadcn.com/docs/installation/next
- https://ui.shadcn.com/docs/components-json
- https://tailwindcss.com/docs/installation/framework-guides/nextjs

Use official version-matched docs for any framework behavior that might have changed.
