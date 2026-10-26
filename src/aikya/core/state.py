"""Private local execution metadata. No prompts, tool outputs or project writes."""
from __future__ import annotations
import hashlib,json,os,re,tempfile,time,uuid
from contextlib import contextmanager
from pathlib import Path
from aikya.middleware.commands import PHASES,recipe
STATES=frozenset(('pending','running','waiting','completed','failed','skipped','blocked','interrupted'))
TERMINAL=frozenset(('completed','failed','blocked','interrupted'))

def text(value,limit=240):
    if not isinstance(value,str):raise ValueError('Expected text metadata')
    return ''.join(c for c in value if c.isprintable() and c not in '\r\n\t')[:limit]

def identity(context):
    if not isinstance(context,dict) or not isinstance(context.get('root'),str) or not context['root']:raise ValueError('Missing project root')
    session=context.get('session_id') or 'local'
    if not isinstance(session,str) or len(session)>180:raise ValueError('Invalid session ID')
    return hashlib.sha256((str(Path(context['root']).resolve())+'\0'+session).encode()).hexdigest()

def directory(context,create=False):
    base=Path(context.get('cache_root') or os.environ.get('AIKYA_EXECUTION_CACHE') or (Path(tempfile.gettempdir())/('aikya-execution-'+str(getattr(os,'getuid',lambda:0)())))).absolute()
    if any(p.is_symlink() for p in (base,*base.parents) if p not in (Path('/var'),Path('/tmp'))):raise ValueError('Unsafe execution cache')
    base=base.resolve()
    target=base/identity(context)
    if target.is_symlink():raise ValueError('Unsafe execution cache')
    if create:
        base.mkdir(mode=0o700,parents=True,exist_ok=True)
        if hasattr(os,'getuid') and base.stat().st_uid!=os.getuid():raise ValueError('Execution cache has another owner')
        target.mkdir(mode=0o700,exist_ok=True)
    return target

def read(path):
    if path.is_symlink():raise ValueError('Symlinked execution state')
    if not path.exists():return None
    if not path.is_file() or path.stat().st_size>2_000_000:raise ValueError('Invalid execution snapshot')
    data=json.loads(path.read_text(encoding='utf8'))
    if not isinstance(data,dict):raise ValueError('Invalid execution snapshot')
    return data

def atomic(path,data):
    if path.is_symlink():raise ValueError('Symlinked execution destination')
    raw=json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    if len(raw.encode('utf8'))>2_000_000:raise ValueError('Execution metadata exceeds the local cache limit')
    fd,name=tempfile.mkstemp(prefix='.aikya-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf8') as stream:stream.write(raw)
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

@contextmanager
def locked(folder):
    # Advisory OS locks release on process death; no orphan O_EXCL lock after a crash.
    path=folder/'.lock'
    if path.is_symlink():raise ValueError('Symlinked execution lock')
    fd=os.open(path,os.O_CREAT|os.O_RDWR|getattr(os,'O_NOFOLLOW',0),0o600)
    deadline=time.monotonic()+3
    try:
        try:import fcntl
        except ImportError:fcntl=None
        if fcntl:
            while True:
                try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);break
                except BlockingIOError:
                    if time.monotonic()>=deadline:raise ValueError('Execution cache busy; retry without changing project files')
                    time.sleep(.01)
        else:
            import msvcrt
            if os.fstat(fd).st_size==0:os.write(fd,b'0')
            while True:
                try:os.lseek(fd,0,0);msvcrt.locking(fd,msvcrt.LK_NBLCK,1);break
                except OSError:
                    if time.monotonic()>=deadline:raise ValueError('Execution cache busy; retry')
                    time.sleep(.01)
        yield
    finally:os.close(fd)

def run_path(context):
    ident=context.get('run_id')
    if not isinstance(ident,str) or not re.fullmatch(r'[a-zA-Z0-9-]{1,80}',ident):raise ValueError('Invalid run ID')
    return directory(context)/(ident+'.json')

def read_active(context):
    folder=directory(context);active=read(folder/'active.json')
    return read_snapshot({**context,'run_id':active['run_id']}) if active else None

def read_snapshot(context):
    state=read(run_path(context))
    if state and (state.get('schema')!=1 or state.get('identity')!=identity(context)):raise ValueError('Execution context mismatch')
    if state:
        phases=state.get('phases');history=state.get('history');seen=state.get('seen')
        if not isinstance(phases,dict) or set(phases)!=set(PHASES) or any(not isinstance(p,dict) or p.get('status') not in STATES or not isinstance(p.get('evidence'),list) or not isinstance(p.get('actors'),dict) for p in phases.values()):raise ValueError('Invalid execution phases')
        if not isinstance(history,list) or len(history)>500 or not isinstance(seen,list) or len(seen)>2000 or not isinstance(state.get('actors'),dict) or type(state.get('revision')) is not int or state['revision']<0 or state.get('phase') not in (*PHASES,None) or state.get('status') not in STATES:raise ValueError('Invalid execution snapshot')
    return state

def start_run(context,command,*,methodology='odd',preview=False,security_required=None,review_required=False):
    selected=recipe(command,methodology,preview=preview,security_required=security_required,review_required=review_required)
    folder=directory(context,True);ident=uuid.uuid4().hex;now=time.time()
    phases={p:{'status':'pending' if p in selected['required'] else 'skipped',
               'reason':'' if p in selected['required'] else 'Not applicable to this invocation','evidence':[],'actors':{}} for p in PHASES}
    state={'schema':1,'identity':identity(context),'run_id':ident,'command':selected['command'],
           'methodology':selected['methodology'],'status':'running','phase':None,'activity':'',
           'invocation_key':context.get('invocation_key'),'candidate_generation':0,'cli_attached':False,'revision':0,'started_at':now,'updated_at':now,'phases':phases,'history':[],'seen':[],'actors':{}}
    with locked(folder):
        previous=read_active(context)
        if previous and previous['status'] not in TERMINAL and context.get('invocation_key') and previous.get('invocation_key')==context['invocation_key'] and previous['command']==command:return previous
        if previous and previous['status'] not in TERMINAL:
            previous.update(status='interrupted',reason='Superseded by a new explicit invocation',updated_at=now,revision=previous['revision']+1)
            atomic(folder/(previous['run_id']+'.json'),previous)
        atomic(folder/(ident+'.json'),state);atomic(folder/'active.json',{'run_id':ident})
    return state

def evidence_valid(phase,values):
    if not isinstance(values,list) or not values or len(values)>40:return False
    for item in values:
        if not isinstance(item,dict) or not isinstance(item.get('check'),str) or not item['check'].strip():return False
        if phase=='review':
            if item.get('kind')!='review' or item.get('result')!='passed' or not item.get('reviewer') or not re.fullmatch(r'[a-f0-9]{64}',str(item.get('candidate',''))):return False
        elif phase in ('validate','security'):
            if item.get('kind')=='process':
                if type(item.get('exit_code')) is not int or item['exit_code']!=0:return False
            elif item.get('kind')!='inspection' or item.get('result')!='passed':return False
        elif item.get('result') not in ('recorded','passed'):return False
    return True

def record_event(context,event):
    if not isinstance(event,dict):raise ValueError('Invalid execution event')
    phase=event.get('phase');status=event.get('status')
    if phase not in PHASES or status not in STATES:raise ValueError('Unknown phase or status')
    reason=text(event.get('reason',''),500)
    if status in ('skipped','blocked','failed','waiting','interrupted') and not reason:raise ValueError('A reason is required')
    evidence=event.get('evidence',[])
    if not isinstance(evidence,list) or len(evidence)>40:raise ValueError('Invalid evidence metadata')
    if status=='completed' and not evidence_valid(phase,evidence):raise ValueError('Completion requires actual successful checks or recorded observations')
    clean_evidence=[]
    for value in evidence:
        if not isinstance(value,dict):raise ValueError('Invalid evidence metadata')
        clean_evidence.append({k:(v if type(v) is int else text(v,500)) for k,v in value.items() if k in ('kind','result','check','exit_code','reviewer','candidate','path')})
    ident=event.get('id') or uuid.uuid4().hex
    if not isinstance(ident,str) or not re.fullmatch(r'[\w-]{1,100}',ident):raise ValueError('Invalid event ID')
    folder=directory(context,True)
    with locked(folder):
        state=read_snapshot(context)
        if not state:raise ValueError('Execution was not started')
        active=read(folder/'active.json')
        if not active or active.get('run_id')!=context.get('run_id'):raise ValueError('Invocation superseded; ignore late event')
        if ident in state['seen']:return state
        if state['status'] in TERMINAL:raise ValueError('Execution is closed; start a new run')
        expected=event.get('expected_revision')
        if expected is not None and (type(expected) is not int or expected!=state['revision']):raise ValueError('Execution revision changed')
        actor=text(event.get('actor_id','main'),100);model=event.get('observed_model')
        if model is not None:model=text(model,120)
        generation=state.get('candidate_generation',0)
        expected_generation=event.get('candidate_generation')
        if expected_generation is not None and (type(expected_generation) is not int or expected_generation!=generation):raise ValueError('Candidate changed; stale check result rejected')
        if status=='completed' and phase in ('validate','security','review'):
            bound=expected_generation if expected_generation is not None else state['phases'][phase]['actors'].get(actor,{}).get('candidate_generation')
            if type(bound) is not int or bound!=generation:raise ValueError('Completion requires the current candidate generation')
        if status=='running' and phase in ('explore','plan','implement'):
            generation+=1;state['candidate_generation']=generation
            for p in PHASES[PHASES.index(phase)+1:]:
                if state['phases'][p]['status'] not in ('pending','skipped'):
                    state['phases'][p].update(status='pending',reason='Candidate changed; repeat affected verification',evidence=[])
        now=time.time();entry={'id':ident,'phase':phase,'status':status,'reason':reason,'actor_id':actor,
                               'activity':text(event.get('activity','')),'source':text(event.get('source','explicit'),80),
                               'observed_model':model,'evidence':clean_evidence,'at':now,'candidate_generation':generation}
        current=state['phases'][phase];current.update(status=status,reason=reason,evidence=clean_evidence)
        current['actors'][actor]={'observed_model':model,'updated_at':now,'status':status,'evidence':clean_evidence,'candidate_generation':generation}
        actor_states=[v['status'] for v in current['actors'].values() if v.get('candidate_generation')==generation]
        if status=='completed' and any(v not in ('completed','skipped') for v in actor_states):
            current.update(status='failed' if 'failed' in actor_states else 'running',reason='Other actors remain unfinished or failed')
        state.update(phase=phase,actor_id=actor,status='waiting' if status=='waiting' else 'running',activity=entry['activity'],updated_at=now,revision=state['revision']+1)
        state['history']=(state['history']+[entry])[-500:];state['seen']=(state['seen']+[ident])[-2000:]
        atomic(run_path(context),state)
        return state

def finish_run(context,status,reason=''):
    if status not in TERMINAL:raise ValueError('Invalid final status')
    folder=directory(context,True)
    with locked(folder):
        state=read_snapshot(context)
        if not state:raise ValueError('Missing execution')
        if state['status'] in TERMINAL:
            if state['status']==status:return state
            raise ValueError('Execution is closed; start a new reviewed invocation')
        active=read(folder/'active.json')
        if not active or active.get('run_id')!=context.get('run_id'):raise ValueError('Invocation superseded')
        if status=='completed' and any(p['status'] not in ('completed','skipped') for p in state['phases'].values()):raise ValueError('Required phases remain incomplete or failed')
        if status!='completed' and not reason:reason='Execution '+status
        state.update(status=status,reason=text(reason,500),updated_at=time.time(),revision=state['revision']+1)
        atomic(run_path(context),state)
    return state


def record_actor(context,actor_id,metadata):
    """Observed agent identity/lifecycle; a stop does not imply successful review."""
    actor=text(actor_id,100)
    if not actor:raise ValueError('Missing actor identity')
    folder=directory(context,True)
    with locked(folder):
        value=read_snapshot(context);active=read(folder/'active.json')
        if not value or not active or active.get('run_id')!=context.get('run_id') or value['status'] in TERMINAL:return value
        row={k:text(v,120) for k,v in metadata.items() if k in ('actor_type','observed_model','status','source') and isinstance(v,str)}
        value['actors'].setdefault(actor,{}).update(row,updated_at=time.time())
        value.update(updated_at=time.time(),revision=value['revision']+1);atomic(run_path(context),value)
        return value


def attach_cli(context,command,methodology,preview=False):
    """Claim a just-started hook invocation, so the support CLI is not a second command."""
    folder=directory(context)
    if not folder.is_dir():return None
    with locked(folder):
        value=read_active(context)
        if not value or value['command']!=command or value['status'] in TERMINAL or value['history'] or value.get('cli_attached'):return None
        selected=recipe(command,methodology,preview=preview)
        for name,phase in value['phases'].items():
            phase.update(status='pending' if name in selected['required'] else 'skipped',reason='' if name in selected['required'] else 'Not applicable to this invocation')
        value.update(methodology=selected['methodology'],cli_attached=True,revision=value['revision']+1,updated_at=time.time())
        atomic(folder/(value['run_id']+'.json'),value);return value
