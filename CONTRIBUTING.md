# Contributing to Aikya Harness

Thank you for improving Aikya Harness. We welcome contributions that advance
the quality, safety, accessibility, documentation and extensibility of
AI-assisted software, infrastructure and DevOps engineering.

## 1. Ways to contribute
Contributions include bug reports, documentation, Agent Skills, Claude Code
subagents, command improvements, language/framework support, infrastructure
capabilities, tests, security hardening and feature proposals.

## 2. Before you start
Read README.md, SECURITY.md, CODE_OF_CONDUCT.md and relevant code.
Search for existing issues and discuss large architectural changes before
implementing. Never include credentials, private data or proprietary code.

## 3. Repository structure
- aikya-skills/: public /aikya-* commands and safe user workflows.
- engineering/agents/: curated technical subagents.
- engineering/skills/: stack-specific Agent Skills.
- template/: project-local agents, skills, hooks, rules, scripts and scaffolding.
- install.py and aikya_cli.py: safe onboarding and project runtime.
- aikya_analyze.py and project_discovery.py: evidence-based existing-project adoption.
- doc_bootstrap.py and docs_templates_en.py/docs_templates_es.py:
  deterministic Aikya living documentation.
- docs_language.py: EN/ES living-doc policy under .aikya/docs-policy.json.
- scripts/ci/: release, asset, metadata and quality validation.
- tests/: compatibility, regression, safety and project profiles.
- examples/: approved example decisions, not fabricated applications.

## 4. Development workflow
1. Branch from develop or the approved target feature branch.
2. Define observable acceptance criteria and verify existing behavior.
3. Make small scoped changes with automated tests and documentation.
4. Preserve compatibility with existing profiles and customized agents/skills.
5. Run the configured tests, catalog validation and profile smoke checks.
6. Submit a reviewable pull request into the agreed base branch.
7. Never create tags/releases or execute remote deployments from ordinary PRs.

## 5. Engineering conventions
- English is mandatory for code comments, docstrings, prompts, runtime messages,
  agents, skills, CLI, GitHub community files and public repository documentation.
- ONLY markdown documentation generated or maintained under aikya/docs/ may use
  en or es, selected through /aikya-init or /aikya-analyze.
- Preserve JSON keys, public command names, version identifiers, stable paths,
  existing user files and historical change-log IDs.
- Accept Spanish and English **user input** in classifiers while keeping
  engineering instructions in English.
- Favor stdlib utilities, explicit errors, deterministic behavior, minimal
  dependencies, and clear approval boundaries.

## 6. Agents and Agent Skills
Use Claude Code's native .claude/agents/*.md and .claude/skills/*/SKILL.md
formats. Do not add Managed Agents API resources, remote provisioning or a
custom Messages API tool-use loop.

Define narrow triggering descriptions, realistic tools, bounded delegation,
evidence-based outputs and explicit restrictions on external actions.
Read-only reviewers should not expose editing or arbitrary command tools.
Add relevant positive, negative and permission-boundary tests.

Ensure metadata passes scripts/ci/validate_agent_assets.py.

## 7. Infrastructure and DevOps
Terraform/OpenTofu/Ansible, Docker, Kubernetes, Helm and CI changes need
source-specific validation and a clear rollback plan. Never commit Terraform
state, credentials or production environment values. Remote operations require
separate, informed approval.

## 8. Tests
Run the supported Python matrix, focused tests, example-profile smoke checks,
asset synchronization, release contracts and any affected language/stack checks.
Report checks you could not run as NOT_CONFIGURED or NOT_VERIFIED; never
claim an unobserved success.

## 9. Documentation
Update affected README, CHANGELOG, architecture decisions and living docs.
New Aikya living documentation must follow .aikya/docs-policy.json:
only aikya/docs/ may be Spanish. Historical Spanish documents and request
inputs must remain readable; do not silently overwrite custom documents.

## 10. Commits and pull requests
Use meaningful focused commit messages and provide scope, rationale,
compatibility, actual validation, risk assessment and rollback notes.
Pull requests must not automatically publish releases or deploy infrastructure.

## 11. Security and responsible disclosure
Follow SECURITY.md for private vulnerability reporting. Do not file public
exploit demonstrations or include real secrets in issues and test fixtures.

## 12. Licensing and intellectual property
Contributors must have rights to their submissions under the project's MIT
license. Check licenses, attribution, redistribution conditions and provenance
for any imported third-party agents, skills, documentation or code.

## 13. Code of conduct
All contributors must follow CODE_OF_CONDUCT.md and maintain respectful,
evidence-based technical collaboration.

## 14. Thanks
Every contribution—from a corrected document to a safe infrastructure
integration—helps make Aikya more useful and trustworthy.

## Python source layout

Production code lives in src/aikya/. Group changes by the existing core, tools,
middleware, memory, installation, discovery, workflows, documentation, catalogs,
routing and quality boundaries. Keep CLI compatibility adapters thin. Declarative
assets have one canonical source under src/aikya/resources/; installed paths are
resolved by the shared inventory rather than inferred from the source prefix.

For development, explicitly install the project in an isolated environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

A normal install has no third-party runtime dependency. The agent-loop extra is
optional and requires explicit developer selection. Do not install it just to run
onboarding or ordinary offline tests. Use python -m aikya or the aikya console
script after installation; existing root scripts also work from a source checkout.

Keep every new Aikya plan, bug and feature under aikya/docs/plan/, aikya/docs/bugs/
and aikya/docs/features/. Preserve authoritative SDD dossiers under aikya/docs/specs/.
Use the shared writer, exact Markdown footer and refreshed indice.md. Existing
project-owned documentation must not be moved automatically.

GENERATED BY AIKYA HARNESS
