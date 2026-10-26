"""Public Claude command names and verified legacy replacements."""
BOOTSTRAP_COMMANDS=(
    'aikya-init', 'aikya-analyze', 'aikya-answers', 'aikya-doctor',
    'aikya-project', 'aikya-infra', 'aikya-scaffold',
    'aikya-feature', 'aikya-bugfix', 'aikya-arc-review', 'aikya-mobile-feature',
    'aikya-skills-status', 'aikya-skills-plan', 'aikya-quality', 'aikya-docs', 'aikya-tests',
    'aikya-docs-sync', 'aikya-verify', 'aikya-models', 'aikya-tokens', 'aikya-install-skill',
    'aikya-specify', 'aikya-clarify', 'aikya-plan', 'aikya-tasks', 'aikya-implement', 'aikya-sdd-status', 'aikya-memory',
)

LEGACY_RENAMES={
    'aikya-project-bootstrap':'aikya-infra',
    'aikya-skills':'aikya-skills-status',
    'aikya-project-init':'aikya-project',
    'aikya-infra-project':'aikya-infra',
    'aikya-architecture-review':'aikya-arc-review',
    'aikya-documentation-sync':'aikya-docs-sync',
    'aikya-skills-install':'aikya-install-skill',
}
