"""Local continuity metadata for native host compaction; no summarizer or approval."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
from aikya.core.checkpoints import safe_file, identity
from aikya.core.state import locked, read, atomic, directory

MANUAL = '/compact Keep the goal, decisions, affected paths, ODD/SDD state, pending checks and next step. Omit repeated logs and explanations.'


def location(root, session):
    if not isinstance(session,str) or not session or len(session)>180:
        raise ValueError('Invalid compaction session identity')
    name=hashlib.sha256(session.encode()).hexdigest()+'.json'
    return safe_file(root,'.harness/state/compaction/'+name)


def checkpoint(root, event, execution):
    root=Path(root).resolve();path=location(root,event.get('session_id','local'))
    path.parent.mkdir(parents=True,exist_ok=True)
    with locked(path.parent):
        previous=read(path) or {}
        if previous and previous.get('identity')!=identity(root):raise ValueError('Compaction metadata belongs to another checkout')
        epoch=previous.get('context_epoch',0)
        if event.get('hook_event_name')=='PostCompact':epoch+=1
        execution=execution or {}
        phases=execution.get('phases',{})
        delivered=read(directory({'root':str(root),'session_id':event.get('session_id','local')})/'context-delivery.json') or {}
        source_paths=delivered.get('paths',[])
        if not isinstance(source_paths,list) or len(source_paths)>8:raise ValueError('Invalid continuity source scope')
        for source in source_paths:safe_file(root,source)
        value={'schema':1,'identity':identity(root),'context_epoch':epoch,
               'run_id':execution.get('run_id'),'command':execution.get('command'),
               'methodology':execution.get('methodology'),
               'candidate_generation':execution.get('candidate_generation'),
               'pending_checks':[key for key,row in phases.items() if row.get('status') not in ('completed','skipped')],
               'evidence_references':sorted({v['path'] for row in phases.values() for v in row.get('evidence',[]) if isinstance(v.get('path'),str)})[:20],
               'source_paths':source_paths,'observed_at':time.time()}
        # Only typed identifiers/references from existing execution state are kept;
        # no raw prompt, tool output or native compact_summary is ever copied.
        if len(json.dumps(value))>8000:raise ValueError('Continuity metadata exceeds its limit')
        atomic(path,value)
    return value


def warning(metrics, *, now=None, threshold=75):
    now=time.time() if now is None else now
    observed=metrics.get('observed_at');window=metrics.get('working_window');used=metrics.get('current_context_tokens')
    if (type(observed) not in (int,float) or not 0<=now-observed<=60 or
            type(window) is not int or not 100000<=window<=1000000 or type(used) is not int or used<0):return None
    if used/window*100<threshold:return None
    return 'Verified working context is at least '+str(threshold)+'% full. Consider native '+MANUAL+' Compaction itself uses tokens; prior quota is unchanged.'


def configure_native(root, *, approved=False, supported=False, window=200000):
    if approved is not True:raise ValueError('Explicit project compaction configuration approval required')
    if type(window) is not int or not 100000<=window<=1000000:raise ValueError('Native working window must be 100000–1000000 tokens')
    if not supported:return {'status':'manual_only','manual_command':MANUAL,'writes':False}
    path=safe_file(Path(root).resolve(),'.claude/settings.json')
    current=json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(current,dict):raise ValueError('Custom settings require review')
    if (current.get('autoCompactWindow',window)!=window or current.get('modelSettings') or
            current.get('env',{}).get('CLAUDE_CODE_AUTO_COMPACT_WINDOW')):
        return {'status':'needs_review','writes':False,'reason':'Custom window or per-model/environment override preserved'}
    # Reuse the exact installed observer invocation, including platform quoting.
    hooks=current.get('hooks',{})
    observer=next((h for g in hooks.get('UserPromptSubmit',[]) for h in g.get('hooks',[])
                   if 'execution_observer.py' in str(h.get('command',''))),None)
    if not observer:return {'status':'manual_only','writes':False,'reason':'Install the project execution observer before enabling native auto compaction'}
    current['autoCompactWindow']=window
    if observer:
        for name in ('PreCompact','PostCompact'):
            groups=hooks.setdefault(name,[])
            if not any(observer==h for g in groups for h in g.get('hooks',[])):groups.append({'hooks':[dict(observer)]})
    from aikya.storage import atomic_write
    atomic_write(path,json.dumps(current,indent=2)+'\n')
    return {'status':'configured','writes':True,'requested_window':window,
            'effective_window':None,'hooks_registered':bool(observer),
            'note':'Host managed settings and environment can override this request; effective window is not assumed.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',type=Path,default=Path.cwd());parser.add_argument('--native-auto',action='store_true')
    parser.add_argument('--window',type=int,default=200000);parser.add_argument('--approved',action='store_true')
    args=parser.parse_args(argv)
    if not args.native_auto:
        print(json.dumps({'mode':'manual','manual_command':MANUAL,'writes':False}));return 0
    executable=shutil.which('claude');supported=False
    if executable:
        result=subprocess.run([executable,'--help'],capture_output=True,text=True,timeout=10)
        supported=result.returncode==0 and '--autocompact' in result.stdout
    try:
        result=configure_native(args.target,approved=args.approved,supported=supported,window=args.window)
    except (ValueError,OSError,TypeError,AttributeError) as exc:
        parser.exit(2,str(exc)+'\n')
    print(json.dumps(result))
    return 0
