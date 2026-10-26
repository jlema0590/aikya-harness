"""Deterministic English templates for Aikya living documentation."""
from __future__ import annotations

MARK = ""


def flat(value):
    return str(value).replace("\\", "/").replace("\n", " ").replace("|", "/").strip()


def pages(profile: dict, modules: list[dict]) -> dict[str, str]:
    name = flat(profile["name"])
    kind = profile.get("project_type", "development")
    backend = flat(profile["backend"])
    frontend = flat(profile["frontend"])
    mobile = flat(profile["mobile"])
    architecture = flat(profile["architecture"])
    detected = "\n".join(
        "- " + flat(m["path"]) + ": " + flat(m["role"]) + " / " + flat(m["technology"])
        + " (verify against actual source)" for m in modules
    ) or "No application module was identified."
    values = {
        "aikya/docs/README.md": """# Living documentation — """ + name + """

Documentation is part of each engineering deliverable. Source, infrastructure,
test and architecture changes must update affected pages and a per-request log
with verifiable evidence. Read-only questions do not require documentation changes.

## Index

- [Overview](overview.md)
- [Roadmap](plan/roadmap.md)
- [Features](features/index.md)
- [Bugs](bugs/index.md)
- [Security](security/security.md)
- [Architecture](architecture/overview.md)
- [Deployment](operations/deployment.md)
- [Observability](operations/observability.md)
- [Quality](quality/testing.md)
- [Architecture decisions](decisions/README.md)
- [Change log](changes/README.md)
- [Technical bootstrap](harness/bootstrap.md)
- [Skills](skills.md)
""",
        "aikya/docs/overview.md": f"""# Project overview — {name}

## Purpose
Product objectives and owner requirements have not been verified.
Do not invent business requirements.

## Technical context
- Project type: {kind}
- Mode: {flat(profile['mode'])}
- Repository layout: {flat(profile.get('repository_layout', 'monorepo'))}
- Backend: {backend} ({flat(profile['backend_framework'])})
- Frontend: {frontend}
- Mobile: {mobile} ({flat(profile['mobile_framework'])})
- Architecture: {architecture}
- Data store: {flat(profile['database'])}
- API style: {flat(profile['api_style'])}
- Authentication: {flat(profile['auth'])}
- CI: {flat(profile['ci'])}
- Deployment: {flat(profile['deployment'])}

## Discovered modules
{detected}

## Open decisions
Verify production architecture, owner, SDK versions and critical constraints.
""",
        "aikya/docs/plan/roadmap.md": """# Engineering roadmap

| ID | Task | Status | Verification |
|---|---|---|---|
| PLAN-001 | Review the project profile | Recorded | Profile file present |
| PLAN-002 | Confirm architecture and business goals | Pending | Reviewed ADR |
| PLAN-003 | Implement approved scope | Pending | Changed files and tests |
| PLAN-004 | Verify and document delivered changes | Pending | Actual check results |

Document dependencies, owners, rollout constraints and risks before execution.
""",
        "aikya/docs/features/index.md": """# Feature catalog

Record identifier FEAT-NNN, scope, user story, observable acceptance criteria,
affected endpoints or screens, tests, dependencies and delivery status.
No product features can be inferred solely from framework manifests.
""",
        "aikya/docs/bugs/index.md": """# Bug and incident register

For each defect, record reproduction, expected and actual behavior, root cause,
the smallest supported fix and verified regression test. Do not mark untested
changes as successful.
""",
        "aikya/docs/security/security.md": f"""# Security and privacy

Declared authentication approach: {flat(profile['auth'])}.
Onboarding is not a threat-model review, audit, penetration test or certification.

| ID | Unverified observation | Next action | Status |
|---|---|---|---|
| SEC-001 | Threat model | Review trust boundaries and data flows | Pending |
| SEC-002 | Automated security scans | Review SAST/dependency tooling | Pending |

Validate authorization, secret handling, dependencies, input validation, audit logs,
data retention and least-privilege access without exposing sensitive data.
""",
        "aikya/docs/architecture/overview.md": f"""# Technical architecture

Declared style: {architecture}. Confirm it against the code and constraints.

## Components
{detected}

## Boundaries and contracts
Examine API contracts, domain boundaries, storage, message flows and deployment
dependencies. Do not invent endpoints, external services or runtime links.

## Decisions
See architecture decision records. Update this document when contracts or
system boundaries change.
""",
        "aikya/docs/operations/deployment.md": f"""# Deployment and operations

Target: {flat(profile['deployment'])}. Pipeline: {flat(profile['ci'])}.

A generated template does not prove that a deployment exists. Obtain approval
before contacting external systems, deploying to production, modifying cloud
resources or installing dependencies.

## Readiness
- [ ] Validate target environments, ownership and permissions
- [ ] Review rollback and backup procedures
- [ ] Verify secrets and artifact provenance
- [ ] Test release and recovery procedures
""",
        "aikya/docs/operations/observability.md": f"""# Observability and SRE

Selected approach: {flat(profile['observability'])}.

Define service indicators, structured logs, traces, metrics, alert owners
and runbooks based on deployed behavior. Check PII filtering and propagation.
No telemetry backend or monitoring installation is implied by this page.
""",
        "aikya/docs/quality/testing.md": f"""# Quality and test strategy

Requested strategy: {flat(profile['quality'])}.

Run the checks appropriate to the project and report the actual commands,
results and limits. Distinguish failed, passed, skipped and not-configured checks.
Tests that were not executed must not be reported as passed.
""",
        "aikya/docs/decisions/README.md": """# Architecture decision records

Create sequential ADR identifiers, record context, considered options,
the decision, consequences, approval and validation. Keep established IDs,
relative paths and filenames stable across translations.
""",
        "aikya/docs/decisions/0001-entrevista-stack.md": f"""# ADR-0001 — Initial technical profile

Status: Proposed; requires verification.

## Context
Aikya captured a project profile using new-project decisions or existing
repository evidence.

## Decision
Project type: {kind}; mode: {flat(profile['mode'])}; architecture: {architecture}.
Backend: {backend}; frontend: {frontend}; mobile: {mobile}.

## Consequences
Review versions, interfaces and domain constraints before implementation.
Source: .harness/project-profile.json.
""",
        "aikya/docs/changes/README.md": """# Per-request engineering change log

For each request that changes technical artifacts, write a REQ-*.md file.
Required headings:

## Changes
List the actual changed files and observable behavior.

## Evidence
List verification commands executed, observed outcomes and limitations.

## Updated documents
List the related updated living-documentation paths.

Never include secrets or raw prompts.
""",
        "aikya/docs/harness/skills-comparison.md": """# Agent Skills assessment

Skills follow the SKILL.md structure and are installed by technical profile.
Installed does not mean invoked. Verify provenance, metadata, triggering,
permissions and outcomes before declaring readiness. Do not overwrite
customized skills.
""",
        "aikya/docs/harness/token-policy.md": """# Context and token efficiency

1. Read relevant profile files and specific documentation; avoid bulk reading.
2. Prefer targeted code and graph queries when a trusted index exists.
3. Verify high-impact findings with source evidence.
4. Reuse existing logic without weakening security, tests or accessibility.
5. Delegate only when specialization or context isolation is useful.
6. Record actual checks, risks and documentation changes.
7. Never download or invoke external infrastructure automatically.
8. Auxiliary Haiku models require explicit opt-in; critical decisions remain
   the responsibility of the main model.
""",
    }
    if frontend != "none" or mobile != "none":
        values["aikya/docs/design/design-system.md"] = f"""# Design system and UX

Frontend: {frontend}; mobile: {mobile}. Document actual component patterns,
accessibility states, responsive breakpoints and design tokens after examining
the application. Do not invent a previously implemented design system.
"""
        values["aikya/docs/README.md"] += "\n- [Design system](design/design-system.md)\n"
    infra = profile.get("infrastructure", {})
    if isinstance(infra, dict) and (
        infra.get("iac") not in (None, "none", "existing") or
        infra.get("configuration_management") == "ansible" or
        infra.get("containers", {}).get("enabled", False) or
        infra.get("orchestration") not in (None, "none")
    ):
        values["aikya/docs/infrastructure/README.md"] = """# Infrastructure and DevOps

Infrastructure files are not proof of running environments. Review Terraform
modules, Ansible roles, container specs and Kubernetes configuration statically.
Use /aikya-infra plan and obtain permission before generation or deploy.
Never version Terraform state, secret files or credentials.
"""
        values["aikya/docs/infrastructure/architecture.md"] = f"""# Infrastructure architecture

Cloud provider: {flat(infra.get('provider', 'none'))}
IaC: {flat(infra.get('iac', 'none'))}
Configuration management: {flat(infra.get('configuration_management', 'none'))}
Orchestration: {flat(infra.get('orchestration', 'none'))}
Deployment method: {flat(infra.get('deployment_method', 'none'))}
Environments: {', '.join(flat(x) for x in infra.get('environments', [])) or 'Not verified'}

Validate remote state, IAM, costs and change plans before any operation.
"""
        values["aikya/docs/README.md"] += "\n- [Infrastructure and DevOps](infrastructure/README.md)\n"
    if kind != "development":
        values["aikya/docs/overview.md"] = (
            f"# Project overview — {name}\n\nIndependent {kind} project; "
            "no application code is required. Confirm infrastructure evidence.\n")
        values["aikya/docs/plan/roadmap.md"] = """# Infrastructure / DevOps roadmap

- P0: Verify cloud provider, environments, access and security.
- P1: Review and approve /aikya-infra plan.
- P2: Generate authorized files and validate locally.
- P3: Deploy only with separate explicit approval.
"""
        values["aikya/docs/features/index.md"] = """# Infrastructure and deployment capabilities

Inventory real Terraform modules, Ansible roles, containers and orchestration.
Do not invent application features.
"""
        values["aikya/docs/README.md"] += (
            f"\n**{kind.title()} mode:** do not generate application scaffolding. "
            "Use /aikya-infra plan.\n")
    from aikya.documentation.layout import template_pages
    return template_pages(profile, modules, values, 'en')
