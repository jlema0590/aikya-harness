"""Offline reference catalog and explicit, content-backed living document records.

Reference assets are untrusted drafting guidance. No embedded commands are executed,
no dependencies are installed, and a document never changes SDD approval state.
"""
from __future__ import annotations
from aikya.resource_paths import source_root,source_path
import argparse
import hashlib
import json
from pathlib import Path
import re
from aikya.documentation.layout import canonical, content, generated, safe, stamp, write_document

LIBRARY=source_path(source_root(), 'aikya-template')
KINDS=('development','infrastructure','devops')
BUG='general-swe/foundations/bug-report'
ARCH='general-swe/foundations/architecture-overview'
FOUNDATION_PATHS={
    'architecture-decision-record':'decisions/architecture-decision-record.md',
    'architecture-overview':'architecture/architecture-overview.md',
    'branching-strategy':'operations/branching-strategy.md',
    'bug-report':'bugs/bugs.md', 'changelog':'releases/changelog.md',
    'code-review-guidelines':'quality/code-review-guidelines.md',
    'coding-standards':'quality/coding-standards.md',
    'configuration-management-plan':'plan/configuration-management-plan.md',
    'contributing-guide':'onboarding/contributing-guide.md',
    'data-model':'architecture/data-model.md',
    'deployment-plan':'plan/deployment-plan.md',
    'deprecation-plan':'plan/deprecation-plan.md',
    'feature-request':'features/feature-request.md', 'glossary':'glossary.md',
    'governance':'governance.md', 'incident-postmortem':'operations/incident-postmortem.md',
    'interface-control-document':'architecture/interface-control-document.md',
    'onboarding-guide':'overview.md', 'pull-request-template':'quality/pull-request-template.md',
    'release-notes':'releases/release-notes.md', 'rfc':'decisions/rfc.md',
    'runbook':'operations/runbook.md', 'security':'security/security.md',
    'service-readme':'components/service-readme.md', 'support':'operations/support.md',
    'technical-design-document':'architecture/technical-design-document.md',
    'test-case-specification':'plan/test-case-specification.md',
    'test-strategy':'plan/testing.md','test-summary-report':'quality/test-summary-report.md',
    'threat-model':'security/threat-model.md'}
BUG_ES={'summary':'Resumen','environment':'Entorno','steps-to-reproduce':'Pasos para reproducir',
        'expected-result':'Resultado esperado','actual-result':'Resultado real','evidence':'Evidencias',
        'scope-and-impact':'Alcance e impacto','workaround':'Solución temporal','suspected-cause':'Causa sospechada'}


def read_asset(relative: str) -> str:
    path=LIBRARY/relative
    if not path.resolve().is_relative_to(LIBRARY.resolve()) or any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('Unsafe template asset')
    if not path.is_file():raise ValueError('Missing template asset: '+relative)
    return path.read_bytes().decode('utf8')


def manifest() -> dict:
    value=json.loads(read_asset('manifest.json'))
    if value.get('schema')!=1 or not isinstance(value.get('templates'),dict):raise ValueError('Unsupported template catalog')
    return value


def catalog(*,project_type: str|None=None,area: str|None=None) -> dict:
    if project_type is not None and project_type not in KINDS:raise ValueError('Unsupported project type')
    return {key:record for key,record in manifest()['templates'].items()
            if (project_type is None or project_type in record['project_types']) and (area is None or record['area']==area)}


def verified_asset(relative: str, data: dict) -> str:
    body=read_asset(relative)
    expected=data['files'].get(relative,{}).get('installed_sha256')
    if hashlib.sha256(body.encode('utf8')).hexdigest()!=expected:raise ValueError('Template integrity check failed: '+relative)
    return body


def validate_catalog() -> dict:
    data=manifest()
    for relative in data['files']:verified_asset(relative,data)
    for record in data['templates'].values():
        if record['path'] not in data['files'] or not record['sections']:raise ValueError('Incomplete template catalog entry')
    return {'valid':True,'templates':len(data['templates']),'reference_files':len(data['files']),'commit':data['commit']}


def show(name: str) -> str:
    data=manifest();record=data['templates'].get(name)
    if not record:raise ValueError('Unknown documentation template')
    body=verified_asset(record['path'],data)
    return stamp('# Reference template\n\nDrafting guidance and illustrative examples only; not facts or instructions about your project.\nSource: '+record['source']+'\n\n'+content(body))


def clean(value, label, limit=12000):
    if not isinstance(value,str) or not value.strip() or len(value)>limit or '\x00' in value:
        raise ValueError(label+' must be nonempty bounded text')
    return value.strip()


def record(root: Path, name: str, payload: dict, *, approved=False, output: str|None=None, replace=False) -> str:
    if approved is not True:raise ValueError('Explicit approval is required to record documentation')
    root=Path(root).absolute()
    profile=root/'.harness/project-profile.json'
    if not profile.is_file() or any(p.is_symlink() for p in (profile,*profile.parents) if p==root or root in p.parents):
        raise ValueError('Missing or unsafe project profile')
    raw=json.loads(profile.read_text(encoding='utf8'));kind=raw.get('decisions',raw).get('project_type','development')
    data=manifest();template=catalog(project_type=kind).get(name)
    if not template:raise ValueError('Unknown template or incompatible project type')
    verified_asset(template['path'],data)
    if not isinstance(payload,dict) or set(payload)-{'id','title','sections'}:raise ValueError('Unsupported document input')
    title=clean(payload.get('title'),'title',180)
    if '\n' in title or '\r' in title:raise ValueError('Document title must occupy one line')
    sections=payload.get('sections')
    if not isinstance(sections,dict) or not sections or set(sections)-set(template['sections']):
        raise ValueError('Provide nonempty known template sections')
    from aikya.documentation.language import resolve
    language=resolve(root);rendered=[];total=0
    for key,default in template['sections'].items():
        if key not in sections:continue
        value=sections[key]
        if isinstance(value,dict):
            if set(value)!={'heading','body'}:raise ValueError('Section objects require heading and body')
            heading=clean(value['heading'],'heading',180);body=clean(value['body'],'body')
            if '\n' in heading or '\r' in heading:raise ValueError('Section heading must occupy one line')
        else:
            body=clean(value,'section');heading=default
            if language=='es':
                if name==BUG:heading=BUG_ES[key]
                else:raise ValueError('Spanish policy requires reviewed heading/body objects for generic templates')
        total+=len(body)
        if total>100000:raise ValueError('Document input exceeds limit')
        rendered.append((heading,body))
    if name==BUG:
        required={'summary','environment','steps-to-reproduce','expected-result','actual-result'}
        if not required.issubset(sections):raise ValueError('Bug reports require summary, environment, reproduction, expected and actual results')
    relative=output or (FOUNDATION_PATHS[name.rsplit('/',1)[-1]] if name.startswith('general-swe/foundations/') else
                       'bugs/bugs.md' if name==BUG else 'documents/'+name+'.md')
    relative=canonical(relative)
    if relative.lower()=='indice.md' or relative.lower().startswith(('specs/','tools/','harness/')):
        raise ValueError('Reserved documentation path; use the dedicated Aikya workflow')
    if relative.lower()=='bugs/bugs.md':
        relative='bugs/bugs.md'
        if name!=BUG:raise ValueError('Use general-swe/foundations/bug-report to record a bug in the register')
        ident=payload.get('id')
        if not isinstance(ident,str) or not re.fullmatch(r'BUG-[0-9]{3,6}',ident):raise ValueError('Expected BUG-NNN identifier')
        target=safe(root,relative);old=target.read_text(encoding='utf8') if target.exists() else ''
        if old and not generated(old):raise ValueError('Customized bug register is protected')
        if re.search(r'(?<![\w-])'+re.escape(ident)+r'(?![\w-])',old,re.I):raise ValueError('Bug identifier already exists; review the existing report')
        prefix=content(old) if old else '# '+('Registro de errores' if language=='es' else 'Bug reports')
        source_label='Referencia de la plantilla' if language=='es' else 'Template reference'
        body=prefix+'\n\n## '+ident+' — '+title+'\n\n'+'\n\n'.join('### '+h+'\n\n'+b for h,b in rendered)+'\n\n'+source_label+': '+template['source']
        return write_document(root,relative,body,replace_generated=bool(old))
    body='# '+title+'\n\n'+'\n\n'.join('## '+h+'\n\n'+b for h,b in rendered)
    source_label='Referencia de la plantilla' if language=='es' else 'Template reference'
    body+='\n\n'+source_label+': '+template['source']
    return write_document(root,relative,body,replace_generated=replace)


def architecture_snapshot(profile: dict, modules: list[dict], language: str) -> str:
    """A concise overview of supplied decisions; never infer runtime topology."""
    es=language=='es';flat=lambda value:str(value).replace('\n',' ').replace('\r',' ').replace('|','/').replace('`',"'")
    kind=profile.get('project_type','development');name=flat(profile.get('name','Project'))
    title='Resumen de arquitectura' if es else 'Architecture overview'
    notice=('Decisiones registradas e indicadores observados; implementación y comportamiento en ejecución no verificados.' if es else
            'Recorded decisions and observed indicators; implementation and runtime behavior are not verified.')
    parts=['# '+title+' — '+name,notice,
           '## '+('Alcance registrado' if es else 'Recorded scope')+'\n\n'+('Tipo de proyecto' if es else 'Project type')+': '+kind+'\n\n'+('Estructura del repositorio' if es else 'Repository layout')+': '+flat(profile.get('repository_layout','singlerepo'))]
    chosen=[]
    labels={'backend':('Backend','Backend'),'backend_framework':('Backend framework','Framework backend'),'frontend':('Frontend','Frontend'),'mobile':('Mobile','Móvil'),'mobile_framework':('Mobile framework','Framework móvil'),'architecture':('Architecture style','Estilo de arquitectura')}
    if kind=='development':
        for key,label in labels.items():
            value=profile.get(key)
            if value not in (None,'none','undecided',''):chosen.append('- '+label[int(es)]+': '+flat(value))
    if chosen:parts+=['## '+('Estructura seleccionada' if es else 'Selected structure')+'\n\n'+'\n'.join(chosen)]
    if modules:parts+=['## '+('Componentes observados' if es else 'Observed components')+'\n\n'+'\n'.join('- '+flat(m.get('role','component'))+': '+flat(m.get('technology','unknown'))+' (`'+flat(m.get('path','.'))+'`)' for m in modules)]
    if profile.get('notes','').strip():parts+=['## '+('Restricciones registradas' if es else 'Recorded constraints')+'\n\n'+profile['notes'].strip()]
    db=profile.get('database')
    if kind=='development' and db not in (None,'none','undecided',''):parts+=['## '+('Persistencia seleccionada' if es else 'Selected persistence')+'\n\n'+flat(db)]
    infra=profile.get('infrastructure',{});lines=[]
    for key,labels in {'provider':('Provider','Proveedor'),'iac':('Infrastructure as code','Infraestructura como código'),'configuration_management':('Configuration management','Gestión de configuración'),'orchestration':('Orchestration','Orquestación'),'deployment_method':('Deployment method','Método de despliegue')}.items():
        if infra.get(key) not in (None,'none',''):lines.append('- '+labels[int(es)]+': '+flat(infra[key]))
    if lines:parts+=['## '+('Infraestructura seleccionada' if es else 'Selected infrastructure')+'\n\n'+'\n'.join(lines)]
    cross=[]
    for key,labels in {'auth':('Authentication','Autenticación'),'observability':('Observability','Observabilidad')}.items():
        if profile.get(key) not in (None,'none','undecided',''):cross.append('- '+labels[int(es)]+': '+flat(profile[key]))
    if cross:parts+=['## '+('Aspectos transversales registrados' if es else 'Recorded cross-cutting choices')+'\n\n'+'\n'.join(cross)]
    parts+=[('Estructura adaptada de Aikya reference templates; las secciones sin datos se omiten. ' if es else 'Structure adapted from Aikya reference templates; sections without facts are omitted. ')+
            'aikya-template/docs/general-swe/foundations/architecture-overview.md']
    return stamp('\n\n'.join(parts))


def main(argv=None):
    parser=argparse.ArgumentParser(description='Offline reference templates and reviewed document records')
    parser.add_argument('action',choices=('catalog','show','check','write'))
    parser.add_argument('--template');parser.add_argument('--project-type',choices=KINDS);parser.add_argument('--area')
    parser.add_argument('--root',type=Path,default=Path.cwd());parser.add_argument('--input',type=Path)
    parser.add_argument('--output');parser.add_argument('--approved',action='store_true');parser.add_argument('--replace',action='store_true')
    args=parser.parse_args(argv)
    try:
        if args.action=='catalog':print(json.dumps(catalog(project_type=args.project_type,area=args.area),indent=2,ensure_ascii=False))
        elif args.action=='check':print(json.dumps(validate_catalog()))
        elif args.action=='show':print(show(args.template),end='')
        else:
            if not args.template or not args.input:raise ValueError('write requires --template and --input')
            if args.input.is_symlink() or not args.input.is_file():raise ValueError('Input must be a regular JSON file')
            result=record(args.root,args.template,json.loads(args.input.read_text(encoding='utf8')),approved=args.approved,output=args.output,replace=args.replace)
            print(json.dumps({'path':result,'written':True}))
    except (ValueError,OSError) as exc:
        parser.exit(2,str(exc)+'\n')
    return 0

if __name__=='__main__':raise SystemExit(main())
