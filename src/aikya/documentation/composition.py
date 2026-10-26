"""Select and compose Aikya documents with reviewed foundation sections.

This adapter writes documentation only. SDD stages remain in sdd_engine; source
text, examples, proposed checks and recorded outcomes are never executed here.
"""
from __future__ import annotations
import sys
if __name__ == "__main__":sys.dont_write_bytecode = True
import argparse
import json
from pathlib import Path
import posixpath
import re
from urllib.parse import quote
from aikya.documentation.layout import canonical, content, generated, safe, stamp, write_document
import aikya.documentation.templates as library

BASE='general-swe/foundations/'
ROLES={'overview':'onboarding-guide','architecture':'architecture-overview',
       'design':'technical-design-document','decision':'architecture-decision-record',
       'feature':'technical-design-document','strategy':'test-strategy',
       'case':'test-case-specification','summary':'test-summary-report'}
OPTIONS={'aikya-init':('overview','architecture','strategy'),
         'aikya-analyze':('overview','architecture','strategy'),
         'aikya-arc-review':('architecture','decision','design'),
         'aikya-feature':('feature','design','decision'),
         'aikya-mobile-feature':('feature','design'),
         'aikya-bugfix':('bug',), 'aikya-tests':('strategy','case','summary')}
SDD={'aikya-specify':('new','feature'),'aikya-plan':('plan','design'),
     'aikya-tasks':('tasks','tasks'),'aikya-implement':('authorize','tasks'),
     'aikya-sdd-status':('status','evidence')}
ES={
 'Platforms in scope':'Plataformas incluidas','Objective':'Objetivo','Acceptance criteria':'Criterios de aceptación','Template references':'Referencias de plantillas',
 'Evidence files':'Archivos de evidencias','Context and scope':'Contexto y alcance','Goals':'Objetivos',
 'Non-goals':'Fuera de alcance','The design':'Diseño','Alternatives considered':'Alternativas consideradas',
 'Cross-cutting concerns':'Aspectos transversales','Rollout and rollback':'Entrega y reversión','Open questions':'Preguntas abiertas',
 'Day one':'Primer día','First change':'Primer cambio','What we build and why':'Qué construimos y por qué',
 'How we work':'Cómo trabajamos','On-call':'Guardias','Where things are':'Dónde encontrar la información',
 'First 30, 60, 90 days':'Primeros 30, 60 y 90 días',
 'Context and problem statement':'Contexto y problema','Decision drivers':'Factores de decisión',
 'Considered options':'Opciones consideradas','Decision':'Decisión','Consequences':'Consecuencias',
 'Options in detail':'Opciones en detalle','Confirmation':'Confirmación','More information':'Más información',
 'What we are protecting':'Qué protegemos','Cost and confidence at each level':'Coste y confianza en cada nivel',
 'What we test where':'Qué probamos y dónde','What we do not test':'Qué no probamos',
 'Entry and exit conditions':'Condiciones de entrada y salida','Coverage':'Cobertura',
 'Flaky tests':'Pruebas inestables','Non-functional testing':'Pruebas no funcionales',
 'Environments and data':'Entornos y datos','Who does what':'Responsabilidades',
 'Before you write any of these':'Antes de definir los casos','The case list':'Lista de casos',
 'Each case':'Detalle de cada caso','Abstraction level':'Nivel de abstracción',
 'Guard against false positives':'Prevención de falsos positivos','What these cases do not cover':'Qué no cubren estos casos',
 'Recommendation':'Recomendación','Assessment':'Evaluación','What was tested':'Qué se probó',
 'Exploratory sessions':'Sesiones exploratorias','Defects':'Defectos','Residual risk':'Riesgo residual',
 '1. Purpose and scope':'1. Propósito y alcance','2. Quality attributes':'2. Atributos de calidad',
 '3. Constraints':'3. Restricciones','4. Context':'4. Contexto','5. Containers':'5. Unidades ejecutables',
 '6. Runtime behaviour':'6. Comportamiento en ejecución','7. Data':'7. Datos','8. Deployment':'8. Despliegue',
 '9. Cross-cutting concerns':'9. Aspectos transversales','10. Architecture decisions':'10. Decisiones de arquitectura',
 '11. Known problems and direction':'11. Problemas conocidos y evolución','12. Glossary':'12. Glosario'}


def label(heading,language):
    if language=='es':
        if heading not in ES:raise ValueError('Missing reviewed Spanish heading: '+heading)
        return ES[heading]
    if language!='en':raise ValueError('Unsupported documentation language')
    return heading


def foundation(role):
    key=BASE+ROLES[role];data=library.manifest();record=data['templates'][key]
    library.verified_asset(record['path'],data)
    return key,record


def select(profile,command,*,document=None,kind='feature'):
    if not isinstance(profile,dict):raise ValueError('Invalid project profile')
    from aikya.workflows.methodology import normalize_methodology
    project_type=profile.get('project_type','development');method=normalize_methodology(profile.get('methodology'))
    if project_type not in library.KINDS or method not in ('odd','sdd'):raise ValueError('Invalid project profile')
    if not isinstance(command,str):raise ValueError('Invalid workflow command')
    command=command.removeprefix('/')
    if kind not in ('feature','api','database','spec'):raise ValueError('Unsupported change kind')
    if command not in OPTIONS and command not in SDD:raise ValueError('Unknown workflow command')
    if command=='aikya-mobile-feature' and (project_type!='development' or profile.get('mobile','none')=='none'):
        raise ValueError('The mobile workflow requires a selected mobile project')
    if command in SDD and method!='sdd':raise ValueError('Enable SDD explicitly before using this command')
    if method=='sdd' and (command in SDD or command in ('aikya-feature','aikya-mobile-feature','aikya-bugfix') or (command=='aikya-tests' and document is None)):
        if document is not None:raise ValueError('Use the dedicated SDD engine for this workflow')
        action,name=SDD.get(command,('verify','evidence') if command=='aikya-tests' else ('authorize','tasks'))
        if command=='aikya-specify':name=kind
        helpers={'design':BASE+'technical-design-document','tasks':'ai-assisted-development/foundations/task-plan',
                 'evidence':BASE+'test-summary-report'}
        return {'command':command,'engine':'sdd','action':action,'document':name,
                'mode':'read_only' if command=='aikya-sdd-status' else 'explicit_sdd_workflow',
                'templates':['sdd:'+name]+([helpers[name]] if name in helpers else []),'project_type':project_type}
    choices=OPTIONS[command];role=document or choices[0]
    if role not in choices:raise ValueError('Document does not belong to this workflow')
    templates=[library.BUG] if role=='bug' else [foundation(role)[0]]
    if role=='feature':templates.insert(0,'aikya:'+kind+'-acceptance')
    platforms=['android','ios'] if profile.get('mobile')=='both' else [profile['mobile']] if profile.get('mobile','none')!='none' else []
    return {'command':command,'engine':'documentation','document':role,'templates':templates,
            'continuity_engine':'odd_engine' if method=='odd' else None,'available_documents':list(choices),'project_type':project_type,'kind':kind,'platforms':platforms,
            'mode':'read_only' if command=='aikya-arc-review' else 'reviewed_documentation'}


def load_profile(root):
    root=Path(root).absolute();path=root/'.harness/project-profile.json'
    if not path.is_file() or any(p.is_symlink() for p in (path,*path.parents) if p==root or root in p.parents):
        raise ValueError('Missing or unsafe project profile')
    raw=json.loads(path.read_text(encoding='utf8'))
    if not isinstance(raw,dict) or not isinstance(raw.get('decisions',raw),dict):raise ValueError('Invalid project profile')
    return raw.get('decisions',raw)


def slug_value(value):
    if not isinstance(value,str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',value) or len(value)>80:
        raise ValueError('Provide a lowercase descriptive slug')
    return value


def destination(role,slug):
    if role in ('feature','design','decision','case','summary'):slug=slug_value(slug)
    return {'overview':'overview.md','architecture':'architecture/architecture-overview.md',
            'strategy':'plan/testing.md','feature':'features/'+str(slug)+'/spec.md',
            'design':'architecture/designs/'+str(slug)+'.md','decision':'decisions/'+str(slug)+'.md',
            'case':'plan/test-cases/'+str(slug)+'.md','summary':'quality/test-reports/'+str(slug)+'.md'}[role]


def evidence_paths(root,values):
    if not isinstance(values,list) or not values or len(values)>100:raise ValueError('Existing evidence files are required')
    result=[]
    for value in values:
        value=library.clean(value,'evidence path',240);path=Path(value)
        if path.is_absolute() or '\\' in value or any(p in ('','.', '..') for p in value.split('/')):raise ValueError('Unsafe evidence path')
        file=root/path
        if not file.resolve().is_relative_to(root.resolve()) or any(p.is_symlink() for p in (file,*file.parents) if p==root or root in p.parents):raise ValueError('Unsafe evidence path')
        if not file.is_file() or file.stat().st_size==0:raise ValueError('Missing or empty evidence file: '+value)
        result.append(value)
    return result


def split_sections(body):
    """Split real H2 sections, preserving fenced Markdown examples verbatim."""
    intro=[];sections=[];current=intro;fence=None
    for line in content(body).splitlines(keepends=True):
        match=re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$',line)
        if match:
            marker=match[1]
            if fence is None:fence=(marker[0],len(marker))
            elif marker[0]==fence[0] and len(marker)>=fence[1] and not match[2].strip():fence=None
        heading=re.match(r'^## ([^\r\n]+)\s*$',line) if fence is None else None
        if heading:
            block=[heading[1].strip(),[]];sections.append(block);current=block[1]
        else:current.append(line)
    if fence is not None:raise ValueError('Unclosed Markdown fence requires review before merging')
    return ''.join(intro).strip(),[(heading,''.join(lines).strip()) for heading,lines in sections]


def merge_sections(existing,incoming):
    prefix,old=split_sections(existing);new_prefix,new=split_sections(incoming)
    aliases={value:key for key,value in ES.items()}
    identity=lambda value:aliases.get(value,value).casefold()
    replacement={identity(h):(h,b) for h,b in new};result=[];seen=set()
    for heading,body in old:
        key=identity(heading)
        if key in seen:raise ValueError('Duplicate existing document heading requires review: '+heading)
        seen.add(key);result.append(replacement.pop(key,(heading,body)))
    result.extend(replacement.values())
    return stamp((prefix or new_prefix)+'\n\n'+'\n\n'.join('## '+h+'\n\n'+b for h,b in result))


def prose(value,label_name,limit=12000):
    value=library.clean(value,label_name,limit)
    prefix,sections=split_sections(value)
    if sections or re.search(r'^# [^\n]+',prefix,re.M):
        raise ValueError('Use nested H3 headings inside document fields, not H1/H2')
    return value


def render(selection,payload,language,*,root=None,relative=None):
    if not isinstance(payload,dict) or set(payload)-{'title','objective','acceptance','sections','evidence'}:
        raise ValueError('Unknown workflow document fields')
    title=library.clean(payload.get('title'),'title',180)
    if '\n' in title or '\r' in title:raise ValueError('Title must occupy one line')
    role=selection['document'];key,template=foundation(role)
    sections=payload.get('sections',{})
    if not isinstance(sections,dict) or set(sections)-set(template['sections']):raise ValueError('Unknown foundation section')
    parts=['# '+title];is_feature=role=='feature'
    if is_feature:
        objective=prose(payload.get('objective'),'objective',4000)
        acceptance=payload.get('acceptance')
        if not isinstance(acceptance,list) or not 1<=len(acceptance)<=30:raise ValueError('Observable acceptance criteria are required')
        acceptance=[prose(x,'acceptance criterion',1200) for x in acceptance]
        if selection['command']=='aikya-mobile-feature':
            parts+=['## '+label('Platforms in scope',language)+'\n\n'+', '.join(selection['platforms'])]
        parts+=['## '+label('Objective',language)+'\n\n'+objective,
                '## '+label('Acceptance criteria',language)+'\n\n'+'\n'.join('- AC-'+str(i).zfill(2)+': '+x for i,x in enumerate(acceptance,1))]
    elif 'objective' in payload or 'acceptance' in payload:raise ValueError('These fields belong to feature documents')
    if not is_feature and not sections:raise ValueError('Supply actual foundation sections')
    total=0
    for field,heading in template['sections'].items():
        if field not in sections:continue
        value=prose(sections[field],'foundation section');total+=len(value)
        parts+=['## '+label(heading,language)+'\n\n'+value]
    if total>100000:raise ValueError('Foundation content exceeds limit')
    if role=='summary':
        if not {'what-was-tested','assessment'}.issubset(sections):raise ValueError('Summary requires scope and assessment')
        values=evidence_paths(root,payload.get('evidence'))
        note=('Registro de resultados aportados; las comprobaciones no se han ejecutado de forma independiente por este adaptador.' if language=='es' else 'Recorded supplied outcomes; checks are not independently executed by this adapter.')
        links=['- ['+p+']('+quote(posixpath.relpath(p,posixpath.dirname('aikya/docs/'+relative)),safe='/.-_')+')' for p in values]
        parts+=['## '+label('Evidence files',language)+'\n\n'+note+'\n\n'+'\n'.join(links)]
    elif 'evidence' in payload:raise ValueError('Evidence file input belongs to test summaries')
    reference='`'+template['source']+'`'

    parts+=['## '+label('Template references',language)+'\n\n'+reference]
    return stamp('\n\n'.join(parts))


def write(root,command,payload,*,document=None,kind='feature',slug=None,approved=False):
    if approved is not True:raise ValueError('Approval for documentation changes is required')
    root=Path(root).absolute();selection=select(load_profile(root),command,document=document,kind=kind)
    if selection['engine']=='sdd':raise ValueError('Use the dedicated SDD engine; this adapter cannot write SDD stages')
    role=selection['document']
    if role=='bug':return {'path':library.record(root,library.BUG,payload,approved=True),'selection':selection}
    relative=canonical(destination(role,slug));path=safe(root,relative)
    if path.exists() and not generated(path.read_text(encoding='utf8')):raise ValueError('Customized document is protected')
    from aikya.documentation.language import resolve
    body=render(selection,payload,resolve(root),root=root,relative=relative)
    if path.exists():body=merge_sections(path.read_text(encoding='utf8'),body)
    result=write_document(root,relative,body,replace_generated=True)
    return {'path':result,'selection':selection}


def validate_bootstrap_sources():
    for role in ('overview','architecture','strategy'):foundation(role)


def bootstrap(relative,body,profile,modules,language):
    """Compose only recorded onboarding/testing facts; preserve the Aikya base."""
    if relative not in ('overview.md','plan/testing.md'):return body
    es=language=='es'
    if relative=='overview.md':
        from aikya.workflows.methodology import normalize_methodology
        method=normalize_methodology(profile.get('methodology'))
        workflow=('/aikya-specify → /aikya-plan → /aikya-tasks → /aikya-implement' if method=='sdd' else '/aikya-feature / /aikya-bugfix / /aikya-tests')
        how=('Metodología registrada: ' if es else 'Recorded methodology: ')+method+'\n\n'+workflow
        where='`aikya/docs/architecture/architecture-overview.md`\n\n`.harness/project-profile.json`\n\n`harness.json`'
        _,template=foundation('overview')
        extra='\n\n## '+label('How we work',language)+'\n\n'+how+'\n\n## '+label('Where things are',language)+'\n\n'+where
        return stamp(content(body)+extra+'\n\n## '+label('Template references',language)+'\n\n`'+template['source']+'`')
    _,template=foundation('strategy');parts=['# '+('Estrategia de pruebas' if es else 'Test strategy')]
    if profile.get('mode')=='existing':
        paths=profile.get('_documentation_testing_evidence',[])
        if not paths:return body
        parts+=['## '+label('Environments and data',language)+'\n\n'+('Rutas observadas; las pruebas no se han ejecutado ni validado.' if es else 'Observed paths only; tests have not been executed or validated.')+'\n\n'+'\n'.join('- `'+x+'`' for x in paths)]
    else:
        strategy=profile.get('quality')
        if not strategy:return body
        note=('Estrategia declarada; no acredita pruebas ejecutadas.' if es else 'Declared strategy; this is not evidence of executed checks.')
        parts+=['## '+label('What we test where',language)+'\n\n'+str(strategy)+'\n\n'+note]
    parts+=['## '+label('Entry and exit conditions',language)+'\n\n'+('Consulta los checks configurados en `harness.json`; las comprobaciones sin configurar o sin ejecutar permanecen SIN VERIFICAR.' if es else 'Inspect the configured checks in `harness.json`; unconfigured or unexecuted checks remain NOT VERIFIED.'),
            '## '+label('Template references',language)+'\n\n`'+template['source']+'`']
    return stamp('\n\n'.join(parts))


def main(argv=None):
    parser=argparse.ArgumentParser(description='Contextual Aikya and foundations composition')
    parser.add_argument('action',choices=('plan','write'));parser.add_argument('--command',required=True)
    parser.add_argument('--root',type=Path,default=Path.cwd());parser.add_argument('--document',choices=tuple(ROLES)+('bug',))
    parser.add_argument('--kind',choices=('feature','api','database','spec'),default='feature');parser.add_argument('--slug')
    parser.add_argument('--input',type=Path);parser.add_argument('--approved',action='store_true')
    args=parser.parse_args(argv)
    try:
        if args.action=='plan':result=select(load_profile(args.root),args.command,document=args.document,kind=args.kind)
        else:
            if not args.input or args.input.is_symlink() or not args.input.is_file():raise ValueError('Supply reviewed JSON input')
            result=write(args.root,args.command,json.loads(args.input.read_text(encoding='utf8')),document=args.document,kind=args.kind,slug=args.slug,approved=args.approved)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (ValueError,OSError) as exc:parser.exit(2,str(exc)+'\n')

if __name__=='__main__':raise SystemExit(main())
