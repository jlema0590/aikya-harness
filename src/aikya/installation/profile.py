"""Focused installer profile responsibilities."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from aikya.discovery.layout import LAYOUTS,validate_layout
from aikya.discovery.infrastructure import validated as validate_infrastructure
from aikya.installation.defaults import API_STYLES,ARCHS,AUTH,BACKENDS,CIS,DATABASES,DEPLOYS,FRAMEWORKS,FRONTENDS,MOBILES,OBSERVABILITY,PACKAGES,PROJECT_TYPES,RENDERING,TEST_STYLES


def validated(data: dict[str, Any], target: Path) -> dict[str, Any]:
    from aikya.workflows.methodology import normalize_methodology
    data={**data,'methodology':normalize_methodology(data.get('methodology'))}
    choices = {'methodology':['odd','sdd'], 'project_type': list(PROJECT_TYPES), 'mode': ['existing','new'], 'repository_layout': list(LAYOUTS), 'backend': BACKENDS, 'frontend': FRONTENDS,
               'mobile': MOBILES, 'mobile_framework': ['none']+FRAMEWORKS,
               'android_language':['none','kotlin','java'], 'ios_ui':['none','swiftui','uikit'],
               'architecture': ARCHS, 'database':DATABASES, 'ci':CIS,
               'deployment':DEPLOYS, 'package_manager':['none']+PACKAGES,
               'api_style': API_STYLES, 'auth':AUTH, 'observability':OBSERVABILITY,
               'quality':TEST_STYLES, 'frontend_rendering':RENDERING}
    defaults = {'methodology':'odd', 'project_type':'development', 'mode':'new', 'repository_layout':'monorepo', 'backend':'none', 'frontend':'none', 'mobile':'none',
                'mobile_framework':'none', 'android_language':'none', 'ios_ui':'none',
                'architecture':'undecided', 'database':'undecided', 'ci':'undecided',
                'deployment':'undecided', 'package_manager':'npm',
                'quality':'unit+integration', 'notes':'', 'name':target.name,
                'api_style':'undecided', 'auth':'undecided', 'observability':'undecided',
                'backend_framework':'undecided', 'frontend_rendering':'undecided', 'runtime_versions':'',
                'architecture_patterns':[]}
    result = {**defaults, **data}
    for field, values in choices.items():
        if result[field] not in values:
            raise ValueError(f'{field}={result[field]!r} invalid. Options: {values}')
    kind=result['project_type']
    if kind=='development':
        if not any(result[k]!='none' for k in ('backend','frontend','mobile')):
            raise ValueError('Development requires backend, frontend or mobile.')
    else:
        if any(result[k]!='none' for k in ('backend','frontend','mobile')):
            raise ValueError('Standalone infrastructure/DevOps profiles cannot include an application stack. Use development to combine them.')
        if result['mode']=='new' and result['repository_layout']!='singlerepo':
            raise ValueError('Standalone infrastructure/DevOps requires a root without application workspaces.')
    if result['mobile'] == 'none':
        for k in ('mobile_framework','android_language','ios_ui'):
            result[k] = 'none'
    elif result['mobile_framework'] == 'none':
        raise ValueError('Selecciona mobile_framework al habilitar Android/iOS.')
    if result['mobile_framework'] != 'native':
        result['android_language'] = 'none'
        result['ios_ui'] = 'none'
    patterns = result.get('architecture_patterns', [])
    if not isinstance(patterns, list) or any(v != 'event-driven' for v in patterns) or len(patterns) != len(set(patterns)):
        raise ValueError('architecture_patterns only allows a duplicate-free list of event-driven.')
    if not isinstance(result['name'], str) or not result['name'].strip():
        raise ValueError('name must be a nonempty string.')
    if not isinstance(result['notes'], str) or not isinstance(result['runtime_versions'], str):
        raise ValueError('notes y runtime_versions deben ser texto.')
    frameworks = {'none':['none','undecided'], 'java':['undecided','spring-boot','quarkus','micronaut'],
                  'python':['undecided','fastapi','django','flask'],
                  'dotnet':['undecided','aspnet-core','minimal-api'],
                  'node':['undecided','nestjs','fastify','express','hono'],
                  'next':['undecided','next-app-router']}
    if result['backend_framework'] not in frameworks[result['backend']]:
        raise ValueError('backend_framework no coincide con backend.')
    validate_layout(result)
    result['infrastructure'] = validate_infrastructure(result)
    info=result['infrastructure']
    if kind=='infrastructure':
        if info['iac']=='none' and info['configuration_management'] not in ('ansible','existing'):
            raise ValueError('Infrastructure requiere Terraform/OpenTofu o Ansible.')
        if info['containers']['enabled'] or info['orchestration']!='none':
            raise ValueError('Infrastructure-only no despliega contenedores; selecciona DevOps.')
    if kind=='devops' and not (info['containers']['enabled'] or info['orchestration']!='none'):
        raise ValueError('DevOps requiere contenedores o un destino de despliegue.')
    return result
