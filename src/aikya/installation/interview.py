"""Focused installer interview responsibilities."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from aikya.discovery.layout import LAYOUTS,app_count
from aikya.installation.defaults import API_STYLES,ARCHS,AUTH,BACKENDS,CIS,DATABASES,DEPLOYS,FRAMEWORKS,FRONTENDS,MOBILES,OBSERVABILITY,PACKAGES,PROJECT_TYPES,RENDERING,TEST_STYLES


def choice(question: str, values: list[str], default: str) -> str:
    while True:
        print(f'\n{question}')
        for idx, value in enumerate(values, 1):
            print(f'  {idx}. {value}' + (' [por defecto]' if value == default else ''))
        entered = input('Select number or name (Enter = recommended): ').strip().lower()
        if not entered:
            return default
        if entered.isdigit() and 1 <= int(entered) <= len(values):
            return values[int(entered)-1]
        if entered in values:
            return entered
        print('Invalid option; try again.')



def ask(question: str, default: str = '') -> str:
    answer = input(f'{question}' + (f' [{default}]' if default else '') + ': ').strip()
    return answer or default



def yesno(question: str, default: bool = True) -> bool:
    while True:
        value = input(f'{question} [{"Y/n" if default else "y/N"}]: ').strip().lower()
        if not value:
            return default
        if value in ('s', 'si', 'sí', 'y', 'yes'):
            return True
        if value in ('n', 'no'):
            return False
        print('Answer y or n.')



def specialized_interview(target: Path, detected: dict[str, Any], kind: str, mode: str) -> dict[str, Any]:
    """Independent infrastructure interview without application generators."""
    name=ask('Project name',target.name)
    provider=choice('Cloud / on-prem / hybrid',['none','aws','azure','gcp','on-prem','hybrid'],'none')
    infra={'provider':provider,'iac':'none','configuration_management':'none',
           'containers':{'enabled':False,'compose':False},'orchestration':'none',
           'deployment_method':'none','environments':[],'image_repository':'',
           'container_port':None,'source_kind':'none',
           'helm_chart_mode':'create','helm_chart_path':''}
    if kind=='infrastructure':
        infra['iac']=choice('Terraform / OpenTofu / existing / none',['none','terraform','opentofu','existing'],'terraform')
        infra['configuration_management']=choice('Ansible / existing / none',['none','ansible','existing'],'none')
    else:
        infra['source_kind']=choice('Deployment source',['source','image','chart','manifests'],'image')
        docker=yesno('Generate Dockerfile from actual source code?',infra['source_kind']=='source')
        compose=yesno('Generate Docker Compose for local development?',False)
        infra['orchestration']=choice('Destino',['none','kubernetes','cloud-managed','vm'],'kubernetes')
        infra['containers']={'enabled':docker or compose,'compose':compose}
        if infra['orchestration']=='kubernetes':
            infra['deployment_method']=choice('Kubernetes deployment method',['helm','kustomize','yaml'],'helm')
            if infra['deployment_method']=='helm':
                infra['helm_chart_mode']=choice('Helm: create or reuse chart',['create','existing'],'create')
                if infra['helm_chart_mode']=='existing':
                    infra['helm_chart_path']=ask('Relative path of existing chart','infra/helm/charts/app')
        if infra['containers']['enabled'] or infra['orchestration']=='kubernetes':
            infra['image_repository']=ask('Versioned image without credentials (blank=pending)','')
            port=ask('Verified internal port (blank=pending)','')
            infra['container_port']=int(port) if port.isdecimal() else (port or None)
    environments=ask('Comma-separated environments','dev')
    infra['environments']=[v.strip() for v in environments.split(',') if v.strip()]
    return {'methodology':choice('Engineering methodology', ['odd','sdd'], 'odd'), 'project_type':kind,'mode':mode,'name':name,'repository_layout':'singlerepo',
            'backend':'none','frontend':'none','mobile':'none','mobile_framework':'none',
            'backend_framework':'none','architecture':'undecided','database':'undecided',
            'api_style':'undecided','frontend_rendering':'undecided','auth':'undecided',
            'observability':'undecided','android_language':'none','ios_ui':'none',
            'architecture_patterns':[],'package_manager':'none','deployment':'none',
            'quality':'unit+integration','ci':choice('CI/CD',CIS,'undecided'),
            'runtime_versions':'','notes':ask('Additional constraints (optional)',''),
            'infrastructure':infra}



def interview(target: Path, detected: dict[str, Any]) -> dict[str, Any]:
    print('\n=== AIKYA HARNESS TECHNICAL INTERVIEW ===')
    print('Initial observations (not verified builds or tests):')
    for finding in detected['findings']:
        print(' -', finding)
    kind=choice('Aikya project type',list(PROJECT_TYPES),'development')
    # Greenfield interview only; legacy existing data remains valid for analyze.
    mode = 'new'
    if kind!='development':
        return specialized_interview(target,detected,kind,mode)
    technologies = {role: next((m['technology'] for m in detected['modules'] if m['role'] == role), 'none')
                    for role in ('backend', 'frontend', 'mobile')}
    mobile_detected = technologies['mobile']
    mobile_default = 'both' if mobile_detected in ('flutter', 'react-native') else ('android' if mobile_detected == 'android' else ('ios' if mobile_detected == 'ios' else 'none'))
    backend = choice('Primary backend', BACKENDS, 'none')
    frontend = choice('Frontend web', FRONTENDS, 'react' if backend == 'next' else 'none')
    mobile = choice('Mobile platforms', MOBILES, 'none')
    framework = 'none'
    android_language = 'none'
    ios_ui = 'none'
    if mobile != 'none':
        default_framework = mobile_detected if mobile_detected in ('flutter','react-native') else 'native'
        framework = choice('Mobile development framework', FRAMEWORKS, default_framework)
        if framework == 'native' and mobile in ('android', 'both'):
            android_language = choice('Android language', ['kotlin', 'java'], 'kotlin')
        if framework == 'native' and mobile in ('ios', 'both'):
            ios_ui = choice('iOS UI framework', ['swiftui', 'uikit'], 'swiftui')
    if backend == 'none' and frontend == 'none' and mobile == 'none':
        raise ValueError('Select at least one backend, frontend or mobile platform.')
    frameworks = {
        'java': ['undecided','spring-boot','quarkus','micronaut'],
        'python': ['undecided','fastapi','django','flask'],
        'dotnet': ['undecided','aspnet-core','minimal-api'],
        'node': ['undecided','nestjs','fastify','express','hono'],
        'next': ['next-app-router'],
        'none': ['none'],
    }
    backend_framework = choice('Backend framework', frameworks[backend], frameworks[backend][1] if backend in ('java','dotnet','next') else frameworks[backend][0]) if backend != 'none' else 'none'
    api_style = choice('API style', API_STYLES, 'rest') if backend != 'none' else 'undecided'
    frontend_rendering = choice('Web rendering strategy', RENDERING, 'hybrid' if backend=='next' and frontend=='react' else 'spa') if frontend != 'none' else 'undecided'
    layout = choice('Repository layout', list(LAYOUTS),
                    'monorepo' if app_count({'backend':backend, 'frontend':frontend, 'mobile':mobile, 'mobile_framework':framework}) > 1 or (target/'apps').is_dir() else 'singlerepo')
    arch = choice('Preferred architecture', [a for a in ARCHS if a != 'existing'],
                  'modular-monolith')
    event_driven = yesno('Does the project need asynchronous events as an additional architectural pattern?', False)
    database = choice('Database', DATABASES, 'undecided')
    ci = choice('Continuous integration', CIS, 'undecided')
    deployment = choice('Deployment target', DEPLOYS, 'app-stores' if mobile != 'none' and backend == frontend == 'none' else 'undecided')
    pkg_mgr = choice('JS package manager (when relevant)', PACKAGES, 'npm') if backend in ('node','next') or frontend != 'none' or framework == 'react-native' else 'none'
    auth = choice('Identity/authentication', AUTH, 'undecided')
    telemetry = choice('Observabilidad', OBSERVABILITY, 'opentelemetry' if backend != 'none' else 'undecided')
    quality = choice('Test strategy', TEST_STYLES, 'unit+integration')
    infrastructure = {'provider':'none','iac':'none','configuration_management':'none',
                      'containers':{'enabled':False,'compose':False},
                      'orchestration':'none','deployment_method':'none','environments':[],
                      'image_repository':'','container_port':None}
    if yesno('Configure infrastructure and DevOps for this project?', deployment in ('docker','kubernetes')):
        infrastructure['provider'] = choice('Infrastructure provider', ['none','aws','azure','gcp','on-prem','hybrid'], 'none')
        infrastructure['iac'] = choice('Infrastructure as code', ['none','terraform','opentofu','existing'], 'none')
        infrastructure['configuration_management'] = choice('Server configuration management', ['none','ansible','existing'], 'none')
        enabled = yesno('Create Docker containers?', deployment in ('docker','kubernetes'))
        compose = yesno('Use Docker Compose for local development?', False) if enabled else False
        infrastructure['containers'] = {'enabled': enabled, 'compose': compose}
        infrastructure['orchestration'] = choice('Orchestration', ['none','kubernetes','cloud-managed','vm'], 'kubernetes' if deployment=='kubernetes' else 'none') if enabled else 'none'
        if infrastructure['orchestration'] == 'kubernetes':
            infrastructure['deployment_method'] = choice('Kubernetes manifest format', ['helm','kustomize','yaml'], 'helm')
        if infrastructure['iac'] not in ('none','existing') or infrastructure['configuration_management']=='ansible' or infrastructure['orchestration']=='kubernetes':
            environments = ask('Environments (comma-separated; e.g. dev,staging,prod)', 'dev')
            infrastructure['environments'] = [e.strip() for e in environments.split(',') if e.strip()]
        if enabled:
            infrastructure['image_repository'] = ask('Container image (optional, no credentials)', '')
            port = ask('Application internal port (blank if unknown)', '')
            infrastructure['container_port'] = int(port) if port.isdecimal() else (port or None)
    versions = ask('Versions/SDKs to pin (blank = undecided)', '')
    return {'methodology':choice('Engineering methodology', ['odd','sdd'], 'odd'), 'project_type':'development', 'mode': mode, 'repository_layout':layout, 'name': ask('Product/project name', target.name),
            'backend': backend, 'frontend': frontend, 'mobile': mobile,
            'mobile_framework': framework, 'backend_framework':backend_framework, 'api_style':api_style,
            'frontend_rendering':frontend_rendering, 'auth':auth, 'observability':telemetry,
            'runtime_versions':versions, 'android_language': android_language,
            'ios_ui': ios_ui, 'architecture': arch,
            'architecture_patterns':['event-driven'] if event_driven else [], 'database': database,
            'ci': ci, 'deployment': deployment, 'package_manager': pkg_mgr,
            'infrastructure': infrastructure,
            'quality': quality, 'notes': ask('Additional technical constraints or conventions (optional)', '')}
