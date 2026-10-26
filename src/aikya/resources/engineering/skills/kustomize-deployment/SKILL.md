---
name: kustomize-deployment
description: Review safe Kubernetes base and overlay configurations for different environments without cluster access.
---

# Kustomize engineering
1. Inspect bases, overlays, resource patches, generators and API-version compatibility.
2. Avoid environment drift, privilege escalation and plain-text secrets.
3. Validate rendered configuration locally when tools are available; preserve existing manifests unless changes are approved.
4. Never run kubectl apply/delete/patch or contact live clusters automatically.
5. Record manifest paths, local validation and pending approvals in project living documentation.

