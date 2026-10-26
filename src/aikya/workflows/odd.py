"""Durable ODD worklists using reviewed inputs and recorded, not certified, evidence."""
from __future__ import annotations
import argparse,copy,hashlib,json,re,sys,time
sys.dont_write_bytecode=True
from pathlib import Path
from aikya.documentation.layout import generated,content,stamp,write_document,index_paths
from aikya.documentation.composition import slug_value,prose,merge_sections,load_profile
from aikya.workflows.methodology import normalize_methodology
from aikya.core.state import locked,atomic
SOURCE='aikya-template/docs/'
TASK_STATES=('todo','in_progress','done','blocked')

def classify_work(facts: dict) -> dict:
    if not isinstance(facts,dict) or set(facts)-{'understood','contained_risk','resumable_from_request_diff','read_only'} or any(type(v) is not bool for v in facts.values()):raise ValueError('Work facts must be explicit boolean observations')
    if facts.get('read_only'):return {'size':'read_only','reasons':['Investigation only; no implementation artifacts']}
    reasons=[key for key in ('understood','contained_risk','resumable_from_request_diff') if not facts.get(key,False)]
    return {'size':'substantial' if reasons else 'small','reasons':reasons or ['Contained work resumable from request and diff']}

def relative(root,value,must_exist=False):
    if not isinstance(value,str) or not value or len(value)>240 or '\\' in value or Path(value).is_absolute() or any(x in ('','..','.') for x in value.split('/')):raise ValueError('Unsafe project path')
    if any(part=='.env' or part.startswith('.env.') for part in value.split('/')):raise ValueError('Secret files are not evidence or task scope')
    file=root/value
    if any(p.is_symlink() for p in (file,*file.parents) if p==root or root in p.parents) or not file.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe project path')
    if must_exist and (not file.is_file() or file.stat().st_size==0):raise ValueError('Missing or empty evidence file: '+value)
    return file

def digest(path):
    if not path.exists():return None
    if not path.is_file():raise ValueError('Expected regular file')
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def paths(root,ident):
    root=Path(root).absolute();ident=slug_value(ident)
    doc=relative(root,'aikya/docs/features/'+ident+'/spec.md');state=relative(root,'aikya/docs/features/'+ident+'/state.json')
    return root,doc,state

def authorize(root):
    p=load_profile(root)
    if normalize_methodology(p.get('methodology'))!='odd':raise ValueError('ODD cannot replace the dedicated approved SDD workflow')
    if p.get('project_type','development') not in ('development','infrastructure','devops'):raise ValueError('Unsupported project type')
    return p

def normalized(root,raw):
    if not isinstance(raw,dict) or set(raw)-{'title','objective','acceptance','tasks','sections','facts'}:raise ValueError('Unknown ODD input fields')
    title=prose(raw.get('title'),'title',180)
    if '\n' in title or '\r' in title:raise ValueError('Title must occupy one line')
    objective=prose(raw.get('objective'),'objective')
    acceptance=raw.get('acceptance')
    if not isinstance(acceptance,list) or not 1<=len(acceptance)<=30:raise ValueError('Observable acceptance criteria required')
    acceptance=[prose(v,'acceptance',4000) for v in acceptance];criteria={'AC-'+str(i).zfill(2) for i in range(1,len(acceptance)+1)}
    tasks=raw.get('tasks')
    if not isinstance(tasks,list) or not tasks or len(tasks)>100:raise ValueError('A substantial ODD feature requires bounded tasks')
    result=[];ids=set();covered=set()
    for t in tasks:
        if not isinstance(t,dict) or set(t)-{'id','description','acceptance','depends_on','files','checks'}:raise ValueError('Unknown task fields')
        ident=t.get('id')
        if not isinstance(ident,str) or not re.fullmatch(r'TASK-[0-9]{3,6}',ident) or ident in ids:raise ValueError('Unique TASK-NNN IDs required')
        ids.add(ident);record={'id':ident,'description':prose(t.get('description'),'task',2000)}
        for key in ('acceptance','depends_on','files','checks'):
            value=t.get(key,[])
            if not isinstance(value,list) or len(value)>100 or any(not isinstance(v,str) or not v.strip() for v in value) or len(set(value))!=len(value):raise ValueError('Invalid task '+key)
            record[key]=value[:]
        if not record['acceptance'] or not set(record['acceptance']).issubset(criteria):raise ValueError('Tasks must reference known acceptance criteria')
        if not record['files'] or not record['checks']:raise ValueError('Task files and verification steps are required')
        for value in record['files']:relative(root,value)
        record['checks']=[prose(v,'check',800) for v in record['checks']]
        covered.update(record['acceptance']);result.append(record)
    if covered!=criteria:raise ValueError('Tasks must cover every acceptance criterion')
    byid={t['id']:t for t in result}
    def visit(ident,stack,seen):
        if ident not in byid or ident in stack:raise ValueError('Unknown or cyclic task dependency')
        if ident in seen:return
        for dep in byid[ident]['depends_on']:visit(dep,stack|{ident},seen)
        seen.add(ident)
    seen=set()
    for ident in ids:visit(ident,set(),seen)
    sections=raw.get('sections',{})
    if not isinstance(sections,dict):raise ValueError('Invalid feature sections')
    from aikya.documentation.composition import foundation
    keys=foundation('feature')[1]['sections']
    if not set(sections).issubset(keys):raise ValueError('Unknown feature section')
    return {'title':title,'objective':objective,'acceptance':acceptance,'tasks':result,'sections':{k:prose(v,'section') for k,v in sections.items()}}

def summary(data):
    ready=next((t['id'] for t in data['tasks'] if t['status']!='done' and all(next(x for x in data['tasks'] if x['id']==dep)['status']=='done' for dep in t['depends_on'])),None)
    return {**copy.deepcopy(data),'next_task':ready,'status':'recorded_complete' if all(t['status']=='done' for t in data['tasks']) else 'in_progress','independently_executed':False}

def render(data,language):
    from aikya.documentation.composition import render as render_feature,select
    payload={k:data[k] for k in ('title','objective','acceptance','sections')}
    body=render_feature(select({'project_type':data['project_type'],'methodology':'odd'},'aikya-feature'),payload,language)
    es=language=='es';rows=['| Task | Status | Acceptance | Dependencies | Evidence |','|---|---|---|---|---|']
    for t in data['tasks']:
        flat=lambda v:str(v).replace('|','/').replace('\n',' ')
        rows.append('| '+' | '.join(flat(v) for v in (t['id']+' — '+t['description'],t['status'],', '.join(t['acceptance']),', '.join(t['depends_on']),', '.join(t['evidence'])))+' |')
    detail=['## '+('Tareas ODD' if es else 'ODD tasks'),'\n'.join(rows)]
    for t in data['tasks']:
        detail+=['### '+t['id'],('Archivos previstos: ' if es else 'Planned files: ')+', '.join(t['files']),('Comprobaciones previstas (no ejecutadas automáticamente): ' if es else 'Planned checks (not automatically executed): ')+'; '.join(t['checks'])]
    detail+=['## '+('Continuidad ODD' if es else 'ODD continuity'),('Siguiente tarea: ' if es else 'Next task: ')+(summary(data)['next_task'] or ('Ninguna pendiente' if es else 'None pending')),('Resultados registrados; este motor no ejecuta ni certifica las comprobaciones.' if es else 'Recorded outcomes; this engine does not execute or certify checks.'),'`'+SOURCE+'ai-assisted-development/specification/agent-task-specification.md`\n\n`'+SOURCE+'ai-assisted-development/foundations/task-plan.md`']
    return stamp(content(body)+'\n\n'+'\n\n'.join(detail))

def load(root,ident,verify_outcomes=True):
    root,doc,state=paths(root,ident);profile=authorize(root)
    if not state.is_file():raise ValueError('No ODD feature state')
    if state.stat().st_size>2_000_000:raise ValueError('Oversized ODD state')
    d=json.loads(state.read_text())
    allowed={'schema','generated_by','id','revision','project_type','title','objective','acceptance','sections','tasks','history','doc_hash','docs_language'}
    if not isinstance(d,dict) or set(d)!=allowed or d.get('schema')!=1 or d.get('generated_by')!='aikya-odd' or d.get('id')!=ident or type(d.get('revision')) is not int or d['revision']<1:raise ValueError('Invalid/custom ODD state')
    if d['docs_language'] not in ('en','es') or not isinstance(d['history'],list) or len(d['history'])>500:raise ValueError('Invalid ODD state')
    if d['project_type']!=profile.get('project_type','development'):raise ValueError('ODD project type changed; review context')
    task_keys={'id','description','acceptance','depends_on','files','checks','status','evidence','fingerprints','file_fingerprints'}
    if not isinstance(d['tasks'],list) or any(not isinstance(t,dict) or set(t)!=task_keys or t.get('status') not in TASK_STATES for t in d['tasks']):raise ValueError('Invalid persisted tasks')
    raw={k:d[k] for k in ('title','objective','acceptance','sections')};raw['tasks']=[{k:v for k,v in t.items() if k not in ('status','evidence','fingerprints','file_fingerprints')} for t in d['tasks']]
    normalized(root,raw)
    if not doc.is_file() or not generated(doc.read_text()) or digest(doc)!=d['doc_hash']:raise ValueError('ODD document changed externally; reconcile before continuing')
    for t in d['tasks']:
        if not isinstance(t['evidence'],list) or not isinstance(t['fingerprints'],dict) or not isinstance(t['file_fingerprints'],dict):raise ValueError('Invalid recorded evidence')
        if t['status']=='done':
            if not t['evidence'] or set(t['fingerprints'])!=set(t['evidence']) or set(t['file_fingerprints'])!=set(t['files']):raise ValueError('Incomplete task evidence')
            if any(next(x for x in d['tasks'] if x['id']==dep)['status']!='done' for dep in t['depends_on']):raise ValueError('Completed task has incomplete dependencies')
            for value,expected in {**t['fingerprints'],**t['file_fingerprints']}.items():
                if verify_outcomes and digest(relative(root,value,value in t['evidence']))!=expected:raise ValueError('Evidence or affected files changed; review the task outcome')
    return d

def persist(root,ident,data):
    root,doc,state=paths(root,ident);index_paths(root)
    body=render(data,data['docs_language'])
    if doc.exists():
        if not generated(doc.read_text()):raise ValueError('Custom feature document is protected')
        body=merge_sections(doc.read_text(),body)
    old={p:p.read_bytes() if p.is_file() else None for p in (doc,state,root/'aikya/docs/indice.md')}
    data['doc_hash']=hashlib.sha256(body.encode()).hexdigest()
    try:
        write_document(root,'features/'+ident+'/spec.md',body,replace_generated=doc.exists())
        atomic(state,data)
    except Exception:
        for path,value in old.items():
            if value is None:path.unlink(missing_ok=True)
            else:path.write_bytes(value)
        raise
    return summary(data)

def prepare_feature(root,feature_id,reviewed_input,approved=False):
    root,doc,state=paths(root,feature_id);profile=authorize(root)
    if not isinstance(reviewed_input,dict):raise ValueError('Reviewed feature input required')
    classification=classify_work(reviewed_input.get('facts',{}))
    if classification['size']!='substantial':return {'tracking':'request','classification':classification,'writes':False}
    if approved is not True:raise ValueError('Explicit authorization is required')
    packet=normalized(root,reviewed_input);index_paths(root)
    if state.exists():raise ValueError('ODD feature already exists; resume instead of replacing')
    if doc.exists() and not generated(doc.read_text()):raise ValueError('Custom feature document is protected')
    from aikya.documentation.language import resolve
    data={'schema':1,'generated_by':'aikya-odd','id':feature_id,'revision':1,'project_type':profile.get('project_type','development'),'history':[],'doc_hash':'','docs_language':resolve(root),**packet}
    for t in data['tasks']:t.update(status='todo',evidence=[],fingerprints={},file_fingerprints={})
    folder=relative(root,'.harness/state/odd-locks/'+feature_id);folder.mkdir(parents=True,exist_ok=True)
    with locked(folder):
        if state.exists():raise ValueError('ODD feature already exists')
        return persist(root,feature_id,data)

def advance_task(root,feature_id,task_id,result,evidence,expected_revision):
    root,doc,state=paths(root,feature_id);folder=relative(root,'.harness/state/odd-locks/'+feature_id)
    if not state.is_file():raise ValueError('No ODD feature')
    folder.mkdir(parents=True,exist_ok=True)
    with locked(folder):
        data=load(root,feature_id)
        if type(expected_revision) is not int or data['revision']!=expected_revision:raise ValueError('Feature revision changed; reconcile before writing')
        if result not in TASK_STATES:raise ValueError('Unknown task result')
        task=next((t for t in data['tasks'] if t['id']==task_id),None)
        if not task:raise ValueError('Unknown task')
        byid={t['id']:t for t in data['tasks']}
        if result in ('in_progress','done') and any(byid[d]['status']!='done' for d in task['depends_on']):raise ValueError('Complete task dependencies first')
        if not isinstance(evidence,list) or len(evidence)>100 or len(set(evidence))!=len(evidence):raise ValueError('Invalid evidence paths')
        fingerprints={value:digest(relative(root,value,True)) for value in evidence}
        if result=='done' and not fingerprints:raise ValueError('Actual existing evidence files are required')
        if any(value.startswith('aikya/docs/features/'+feature_id+'/') for value in evidence):raise ValueError('A feature cannot certify itself with its own state/document')
        data['history']=(data['history']+[{'task':task_id,'previous':task['status'],'result':result,'recorded_at':time.time(),'evidence':task['evidence'][:]}])[-500:]
        if result!='done':
            invalid={task_id}
            while True:
                more={t['id'] for t in data['tasks'] if set(t['depends_on'])&invalid}
                if more.issubset(invalid):break
                invalid|=more
            for t in data['tasks']:
                if t['id'] in invalid and t['id']!=task_id:t.update(status='todo',evidence=[],fingerprints={},file_fingerprints={})
        task.update(status=result,evidence=evidence[:],fingerprints=fingerprints,file_fingerprints={f:digest(relative(root,f)) for f in task['files']} if result=='done' else {})
        data['revision']+=1
        return persist(root,feature_id,data)

def reconcile_feature(root,feature_id,expected_revision,approved=False):
    """Invalidate stale outcomes only after review; externally edited documents stay protected."""
    if approved is not True:raise ValueError('Explicit reconciliation authorization required')
    root,doc,state=paths(root,feature_id);folder=relative(root,'.harness/state/odd-locks/'+feature_id)
    if not state.is_file():raise ValueError('No ODD feature')
    folder.mkdir(parents=True,exist_ok=True)
    with locked(folder):
        data=load(root,feature_id,verify_outcomes=False)
        if type(expected_revision) is not int or data['revision']!=expected_revision:raise ValueError('Feature revision changed')
        changed=set()
        for task in data['tasks']:
            if task['status']=='done' and any(digest(relative(root,path))!=expected for path,expected in {**task['fingerprints'],**task['file_fingerprints']}.items()):changed.add(task['id'])
        while True:
            more={t['id'] for t in data['tasks'] if set(t['depends_on'])&changed}
            if more.issubset(changed):break
            changed|=more
        if not changed:return summary(data)
        for task in data['tasks']:
            if task['id'] in changed:
                data['history'].append({'task':task['id'],'previous':task['status'],'result':'todo','reason':'Reviewed stale evidence or affected file','evidence':task['evidence'][:],'recorded_at':time.time()})
                task.update(status='todo',evidence=[],fingerprints={},file_fingerprints={})
        data['history']=data['history'][-500:];data['revision']+=1
        return persist(root,feature_id,data)

def resume_feature(root,feature_id):
    try:return summary(load(root,feature_id))
    except (ValueError,OSError,TypeError,KeyError) as exc:return {'status':'needs_review','reason':str(exc),'writes':False}

def main(argv=None):
    sys.dont_write_bytecode=True;p=argparse.ArgumentParser(description='ODD reviewed worklists, recorded evidence and safe resume')
    p.add_argument('action',choices=('classify','new','progress','status','resume','reconcile'));p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--id');p.add_argument('--task');p.add_argument('--result',choices=TASK_STATES);p.add_argument('--revision',type=int);p.add_argument('--input',type=Path);p.add_argument('--evidence',action='append',default=[]);p.add_argument('--approved',action='store_true')
    a=p.parse_args(argv)
    try:
        raw={}
        if a.input:
            if a.input.is_symlink() or not a.input.is_file():raise ValueError('Input must be regular reviewed JSON')
            raw=json.loads(a.input.read_text())
        if a.action=='classify':out=classify_work(raw)
        elif a.action=='new':out=prepare_feature(a.root,a.id,raw,a.approved)
        elif a.action=='progress':
            if not a.approved:raise ValueError('Recording task outcomes requires authorization')
            out=advance_task(a.root,a.id,a.task,a.result,a.evidence,a.revision)
        elif a.action=='reconcile':out=reconcile_feature(a.root,a.id,a.revision,a.approved)
        else:out=resume_feature(a.root,a.id)
        from aikya.middleware.observer import emit_engine_event
        emit_engine_event(a.root,'odd',a.action,out)
        print(json.dumps(out,ensure_ascii=False,indent=2));return 4 if out.get('status')=='needs_review' else 0
    except (ValueError,OSError,TypeError,KeyError) as exc:p.exit(2,str(exc)+'\n')
if __name__=='__main__':raise SystemExit(main())
