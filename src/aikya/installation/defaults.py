"""Installer profile choices and predecessor template signatures."""
from aikya.resource_paths import source_root,source_path
PROJECT_TYPES = ('development', 'infrastructure', 'devops')

HERE = source_root()

TEMPLATE = source_path(HERE, 'template')

V3_TEMPLATE_HASHES = {'scripts/harness/docs_guard.py': '7d67e06379ecc06f59aefdcdde5a81def7b52e47ae904b5a0c0c50d7d205650c', '.claude/agents/frontend-engineer.md': '528a8a1f85da49eea133d14917b70ba51e1ba170833282826bf06ae6f8f062e0', '.claude/agents/mobile-engineer.md': '224a031ae5293358ae642ac87aab2965c7c288bde1cab76233eb2b47308f44d5', '.claude/skills/documentation-sync/SKILL.md': 'eea913b37aa59a7928b45c9820da1e86976331225ea71367199e4baadbeebcbf', '.claude/skills/architecture-review/SKILL.md': 'ee132fb1e1c864b3d897418c999d17ffbe5ccfde2031fb2e64c34f6267acef24', '.claude/skills/bugfix/SKILL.md': 'f888b8594854b63dc73ddad950fbf89c1b775818accfbc603f3d8bf9546c93d4', '.claude/skills/feature/SKILL.md': '87912f2ba37452551e712f00e9de0edded8d9d15420567640ff77bf37de90b9c'}

CANDIDATE_DIRS = ('', 'api', 'backend', 'server', 'web', 'frontend', 'client',
                  'mobile', 'android', 'ios', 'apps/api', 'apps/web', 'apps/mobile',
                  'apps/android', 'apps/ios', 'apps/mobile/android', 'apps/mobile/ios', 'platforms/android', 'platforms/ios',
                  'packages/api', 'packages/web', 'mobile/android', 'mobile/ios')

BACKENDS = ['none', 'java', 'dotnet', 'node', 'next', 'python']

FRONTENDS = ['none', 'react', 'vue', 'angular']

MOBILES = ['none', 'android', 'ios', 'both']

FRAMEWORKS = ['native', 'flutter', 'react-native']

ARCHS = ['existing', 'modular-monolith', 'layered', 'hexagonal', 'clean', 'microservices', 'undecided']

DATABASES = ['undecided', 'none', 'postgresql', 'mysql', 'sqlserver', 'sqlite', 'mongodb', 'other']

CIS = ['undecided', 'github-actions', 'gitlab-ci', 'azure-pipelines', 'jenkins', 'none']

DEPLOYS = ['undecided', 'docker', 'kubernetes', 'serverless', 'cloud-managed', 'app-stores', 'none']

PACKAGES = ['npm', 'pnpm', 'yarn', 'bun']

API_STYLES = ['undecided', 'rest', 'graphql', 'grpc']

AUTH = ['undecided', 'oidc-oauth2', 'jwt', 'session', 'external-idp', 'none']

OBSERVABILITY = ['undecided', 'opentelemetry', 'structured-logging', 'none']

TEST_STYLES = ['unit', 'unit+integration', 'unit+integration+e2e']

RENDERING = ['undecided', 'spa', 'ssr', 'ssg', 'hybrid']
