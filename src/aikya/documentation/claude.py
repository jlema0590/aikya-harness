"""Compose original, profile-specific Claude instructions without executing tools."""
from aikya.resource_paths import source_root,source_path
from pathlib import Path
from aikya.documentation.layout import content, stamp

SOURCE_ROOT=source_root()
ASSET_ROOT=source_path(SOURCE_ROOT, 'claude-templates')
KINDS=('development','infrastructure','devops')


def text(value):
    return str(value).replace('\r',' ').replace('\n',' ').replace('`',"'").replace('|','/').strip()


def asset(path):
    if not path.is_file() or any(part.is_symlink() for part in (path,*path.parents)):
        raise ValueError('Missing or unsafe Claude instruction asset: '+str(path))
    return content(path.read_text(encoding='utf8'))


def render(profile: dict, modules: list[dict]) -> str:
    """Render decisions and observed indicators, never fabricated execution evidence."""
    kind=profile.get('project_type','development')
    if kind not in KINDS:raise ValueError('Unsupported Claude project type')
    layout=profile.get('repository_layout','singlerepo')
    if layout not in ('monorepo','singlerepo'):raise ValueError('Unsupported repository layout')
    from aikya.workflows.methodology import normalize_methodology
    method=normalize_methodology(profile.get('methodology'))
    if method not in ('odd','sdd'):raise ValueError('Unsupported methodology')
    parts=[asset(source_path(SOURCE_ROOT,'template/CLAUDE.md')),
           '## Recorded project decisions\n\n'
           'These onboarding decisions do not prove that code, dependencies or deployments exist.\n\n'
           '- Project: '+text(profile.get('name','Not declared'))+'\n'
           '- Type: '+kind+'; mode: '+text(profile.get('mode','Not declared'))+'\n'
           '- Methodology: '+method+'; layout: '+layout,
           asset(ASSET_ROOT/(kind+'.md'))]
    if layout=='monorepo':
        parts+=['## Monorepo\n\nRespect the recorded workspace boundaries. Inspect manifests before choosing a workspace runner.\nShare code through explicit package contracts; avoid imports into another application’s internals.\nFor new development repositories, the approved scaffold determines apps/, contracts/ and packages/.\nExisting repositories retain their observed directories.']
    else:
        parts+=['## Single repository\n\nKeep the project at its existing or approved root. Aikya support files live under aikya/.\nDo not introduce application workspaces merely to match a template.']
    selected=[]
    if kind=='development':
        for key,label in (('backend','Backend'),('backend_framework','Backend framework'),('frontend','Frontend'),('mobile','Mobile'),('mobile_framework','Mobile framework'),('android_language','Android language'),('ios_ui','iOS UI'),('architecture','Architecture'),('database','Persistence'),('package_manager','JS package manager'),('runtime_versions','Versions/SDK')):
            value=profile.get(key)
            if value not in (None,'','none','undecided'):selected.append('- '+label+': '+text(value))
        guides={
            'java':'Java: inspect the actual JDK, build wrapper, dependency versions and transaction boundaries before changing code.',
            'dotnet':'.NET: inspect SDK constraints, solution/project boundaries, dependency injection and async cancellation.',
            'python':'Python: inspect the existing environment, dependency metadata, imports and test configuration before choosing tools.',
            'node':'Node.js: inspect runtime constraints, package-manager lockfiles, async error handling and shutdown behavior.',
            'next':'Next.js: inspect the installed version and router before changing server/client boundaries, handlers or actions.'}
        if profile.get('backend') in guides:selected.append('- '+guides[profile['backend']])
        frontend=profile.get('frontend')
        if frontend in ('react','vue','angular'):selected.append('- '+frontend.title()+': follow the existing component, state, accessibility and test conventions; inspect rendering boundaries.')
        mobile=profile.get('mobile','none');framework=profile.get('mobile_framework','none')
        if mobile in ('android','both'):selected.append('- Android: inspect lifecycle, SDK/build settings and platform tests; signing and publication require separate authorization.')
        if mobile in ('ios','both'):selected.append('- iOS: inspect lifecycle, Xcode/build settings and platform tests; signing and publication require separate authorization.')
        if framework in ('flutter','react-native'):selected.append('- '+framework+': inspect shared/native boundaries and validate each selected platform independently.')
    info=profile.get('infrastructure',{})
    for key,label in (('provider','Provider'),('iac','Infrastructure as code'),('configuration_management','Configuration management'),('orchestration','Orchestration'),('deployment_method','Deployment method')):
        if info.get(key) not in (None,'','none'):selected.append('- '+label+': '+text(info[key]))
    if info.get('environments'):selected.append('- Environments: '+', '.join(text(x) for x in info['environments']))
    iac=info.get('iac')
    if iac in ('terraform','opentofu'):selected.append('- '+('Terraform' if iac=='terraform' else 'OpenTofu')+': review provider locks, state/backend ownership and a scoped plan before any approved apply; never expose state secrets.')
    if info.get('configuration_management')=='ansible':selected.append('- Ansible: review inventory, privilege escalation and check/diff limitations before an approved run.')
    if info.get('containers',{}).get('enabled'):selected.append('- Containers: inspect build inputs, image provenance, runtime permissions and existing container checks.')
    deployment=info.get('deployment_method')
    if deployment in ('helm','kustomize','yaml'):selected.append('- '+{'helm':'Helm','kustomize':'Kustomize','yaml':'Kubernetes YAML'}[deployment]+': render and review manifests for the intended environment; context, rollout and rollback require explicit review before cluster changes.')
    if selected:parts+=['## Selected stack guidance\n\n'+'\n'.join(selected)]
    rows=['- '+text(m.get('role','component'))+': '+text(m.get('technology','unknown'))+' (`'+text(m.get('path','.'))+'`)' for m in modules]
    parts+=['## Observed module indicators only\n\n'+('\n'.join(rows) if rows else 'No module indicators were recorded. Inspect repository files before choosing commands.')]
    if method=='sdd':parts+=['## SDD workflow\n\nUse /aikya-specify, /aikya-clarify, /aikya-plan and /aikya-tasks before /aikya-implement.\nSpecification, plan and task approvals are separate explicit decisions.\nImplementation requires an approved, dependency-ready task; templates never grant approval.\nUse the installed SDD engine and actual records under aikya/docs/specs/; record real evidence with /aikya-verify.']
    parts+=['## Template reference\n\nAikya composition using the Aikya reference templates agent-instructions structure; project-specific rules and profile adapters belong to Aikya.\naikya-template/docs/ai-assisted-development/foundations/agent-instructions-file.md']
    return stamp('\n\n'.join(parts))
