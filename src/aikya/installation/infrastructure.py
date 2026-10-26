"""Focused installer infrastructure responsibilities."""
from __future__ import annotations
from aikya.documentation.bootstrap import infra_files,_infra_files as infra_source_files
from aikya.documentation.layout import stamp
from aikya.installation.context import InstallationPlan
from aikya.installation.io import safe_write,upgrade_exact_markdown_source


def plan_infrastructure(plan:InstallationPlan,actions:list[str])->None:
    from aikya.documentation.layout import stamp
    context=plan.context
    HERE=context.source_root
    TEMPLATE=context.template_root
    target=plan.target
    profile=plan.profile
    adopt_existing=plan.adopt_existing
    # Inventario local de skills (disponibles != invocadas); conserva documento personalizado.
    from aikya.catalogs.skills import write_inventory
    ok, note = write_inventory(target,profile)
    actions.append(('INVENTARIO ' if ok else 'AVISO ') + note)
    legacy_infra={} if adopt_existing else infra_source_files(profile)
    for rel, content in ({} if adopt_existing else infra_files(profile)).items():
        if rel.endswith('.md') and upgrade_exact_markdown_source(target,legacy_infra[rel].encode('utf8'),target/rel,actions):continue
        if rel == '.gitignore':
            ignore = target/'.gitignore'
            if not ignore.exists():
                safe_write(ignore,content,actions)
            else:
                old=ignore.read_text(encoding='utf8')
                extras=['.harness/state/', '.harness/welcome.json', 'graphify-out/', '.env', '.env.*', '!.env.example']
                missing=[x for x in extras if x not in old.splitlines()]
                if missing:
                    with ignore.open('a',encoding='utf8') as handle:
                        handle.write('\n# Claude Dev Harness v3 (estado local y secretos)\n'+'\n'.join(missing)+'\n')
                    actions.append('AMPLIADO (gitignore) '+str(ignore))
                else:
                    actions.append('SIN CAMBIOS '+str(ignore))
        else:
            safe_write(target/rel,content,actions)
    from aikya.discovery.infrastructure import selected
    if selected(profile['infrastructure']) and not adopt_existing:
        from aikya.tools.infrastructure import plan as infrastructure_plan
        summary=infrastructure_plan(target,profile)
        safe_write(target/'aikya/docs/infrastructure/plan.md',
           stamp(summary), actions,
           replace_managed=True)
