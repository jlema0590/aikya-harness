---
name: helm-deployment
description: Design and locally validate Helm chart templates, value overlays and release configuration without deploying.
---

# Helm deployment engineering
1. Inspect Chart.yaml, templates, dependencies, values and environment overlays.
2. Plan locally safe checks such as helm lint and helm template without unapproved downloads.
3. Avoid secrets in plain-text values; validate least privilege, health probes and upgrade constraints.
4. Never install, upgrade, rollback, uninstall or contact a cluster without explicit authorization.
5. Report manifests, actual validation results and deployment risks in the configured living docs language.

