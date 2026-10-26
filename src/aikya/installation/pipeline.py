"""Focused installer pipeline responsibilities."""
from __future__ import annotations
from aikya.discovery.layout import layout_of
from aikya.installation.context import InstallerContext
from aikya.installation.configuration import apply_profile,configure_project
from aikya.installation.documents import write_living_documents
from aikya.installation.infrastructure import plan_infrastructure
from aikya.installation.preflight import prepare_installation
from aikya.installation.project_assets import activate_engineering,copy_project_template,install_commands


def install(target,profile,detected,dry_run=False,*,adopt_existing=False,docs_lang=None,context=None):
    context=context or InstallerContext()
    plan=prepare_installation(target,profile,detected,adopt_existing,docs_lang,context)
    if dry_run:
        return [f'PLAN: instalar harness en {target}', 'PLAN: crear aikya/docs/, aikya/test/, aikya/scripts/ según '+layout_of(plan.profile)+' y CI/infra', 'PLAN: incorporar hooks por petición + Stop gate y generar receta de scaffold opcional sin ejecutarla', 'PLAN: conservar documentos de usuario y módulos existentes; no instalar dependencias ni desplegar', 'PLAN: integrar Ponytail/Graphify y UI UX Pro Max sólo si hay frontend o móvil, previa aprobación']
    actions=[]
    apply_profile(plan,actions)
    copy_project_template(plan,actions)
    install_commands(plan,actions)
    configure_project(plan,actions)
    write_living_documents(plan,actions)
    activate_engineering(plan,actions)
    plan_infrastructure(plan,actions)
    from aikya.code_index.policy import configure,load_policy
    from aikya.memory.viewer.export import export_view
    policy=configure(target,approved=True,manage_ignore=not adopt_existing,scope=detected.get('analysis_scope','.'))
    if policy.auto_export:
        memory=export_view(target,refresh=policy.enabled,language=plan.documentation_language)
        actions.append('LOCAL MEMORY '+memory.status+': '+memory.html_path)
    elif policy.enabled:
        from aikya.code_index.sync import sync
        sync(target)
        actions.append('LOCAL MEMORY: existing policy keeps automatic HTML export disabled')
    from aikya.documentation.layout import update_index
    update_index(target,plan.documentation_language)
    from aikya.installation.bootstrap.state import record_project_reference
    record_project_reference(target)
    return actions
