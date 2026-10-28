"""Observe explicit Aikya invocations and activity without storing input content."""
from __future__ import annotations
import argparse,hashlib,json,os,re,sys,time
sys.dont_write_bytecode=True
from pathlib import Path
import aikya.core.state as state
from aikya.middleware.commands import recipe

def project_method(root):
    path=Path(root)/'.harness/project-profile.json'
    if path.is_file() and not path.is_symlink():
        raw=json.loads(path.read_text());return raw.get('decisions',{}).get('methodology','odd')
    return 'odd'

def observe(context,event):
    from aikya.middleware.flow_bridge import context as flow_context,publish
    context={**context,**flow_context(context['root'],context.get('session_id'))}
    try:
        from aikya.code_index.hooks import process_event
        process_event(context['root'],event)
    except (ValueError,OSError,TypeError):
        pass  # Memory maintenance never grants approvals or blocks existing gates.
    hook=event.get('hook_event_name');command=None
    prompt_id=event.get('prompt_id')
    invocation_key=hashlib.sha256(prompt_id.encode()).hexdigest() if isinstance(prompt_id,str) and prompt_id else None
    context={**context,'invocation_key':invocation_key}
    if hook=='UserPromptSubmit':
        match=re.match(r'^\s*/(aikya-[a-z-]+)(?:\s|$)',event.get('prompt',''))
        if match:command=match[1]
    elif hook=='PreToolUse' and event.get('tool_name')=='Skill':command=event.get('tool_input',{}).get('skill')
    if command:
        try:recipe(command)
        except ValueError:return None
        context={**context,**flow_context(context['root'],context.get('session_id'),command)}
        active=state.read_active(context)
        if active and active['status'] not in state.TERMINAL and (not context.get('flow_invocation') or active.get('flow_invocation')==context['flow_invocation']):
            if active['command']==command and (hook=='PreToolUse' or (invocation_key and active.get('invocation_key')==invocation_key) or (not invocation_key and not active['history'] and time.time()-active['started_at']<2)):return active
            if hook=='PreToolUse':return state.record_actor({**context,'run_id':active['run_id']},'skill:'+command,{'actor_type':'nested-skill','status':'invoked','source':'hook'})
        value=state.start_run(context,command,methodology=project_method(context['root']))
        try:publish(context,value)
        except (ValueError,OSError,TypeError):pass
        return value
    active=state.read_active(context)
    if not active:return None
    if invocation_key and active.get('invocation_key') and invocation_key!=active['invocation_key']:return active
    c={**context,'run_id':active['run_id']}
    if hook in ('StopFailure','SessionEnd'):
        return state.finish_run(c,'interrupted','Runtime ended before an explicit successful close') if active['status'] not in state.TERMINAL else active
    if hook=='PostToolUseFailure' and active['phase']:
        return state.record_event(c,{'phase':active['phase'],'status':'failed','reason':'Runtime tool reported failure','source':'hook'})
    if hook in ('SubagentStart','SubagentStop'):
        return state.record_actor(c,str(event.get('agent_id') or 'unknown'),{'actor_type':event.get('agent_type') or 'agent','status':'running' if hook=='SubagentStart' else 'stopped','source':'hook'})
    # Tool/agent events are activity, not claims of phase success or model identity.
    return active

def main(argv=None):
    sys.dont_write_bytecode=True
    p=argparse.ArgumentParser(description='Aikya explicit execution transitions and status')
    p.add_argument('action',choices=('start','phase','finish','status','hook'))
    p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--session',default=os.environ.get('CLAUDE_SESSION_ID','local'))
    p.add_argument('--command');p.add_argument('--run');p.add_argument('--phase');p.add_argument('--status');p.add_argument('--reason',default='');p.add_argument('--activity',default='');p.add_argument('--input',type=Path);p.add_argument('--generation',type=int,help='Candidate generation captured before a check/review starts');p.add_argument('--model');p.add_argument('--actor',default='main')
    a=p.parse_args(argv)
    from aikya.middleware.flow_bridge import context as flow_context
    c=flow_context(a.root,a.session,a.command if a.action=='start' else None)
    try:
        if a.action=='start':result=state.start_run(c,a.command,methodology=project_method(c['root']))
        elif a.action=='hook':
            payload=json.load(sys.stdin)
            if not isinstance(payload,dict):raise ValueError('Invalid hook payload')
            c={'root':str(Path(payload.get('cwd') or a.root).resolve()),'session_id':payload.get('session_id') or a.session}
            observe(c,payload);return 0
        else:
            active=state.read_active(c)
            if not active:raise ValueError('No active Aikya execution')
            c['run_id']=a.run or active['run_id']
            if a.action=='status':result=state.read_snapshot(c)
            elif a.action=='finish':result=state.finish_run(c,a.status,a.reason)
            else:
                evidence=[]
                if a.input:
                    if a.input.is_symlink() or not a.input.is_file():raise ValueError('Evidence metadata must be a regular JSON file')
                    evidence=json.loads(a.input.read_text())
                if a.actor=='main' and not a.model:
                    from aikya.middleware.metrics import read_metrics
                    observed=read_metrics(c)
                    if observed and not observed.get('stale'):a.model=observed.get('model')
                result=state.record_event(c,{'candidate_generation':a.generation,'phase':a.phase,'status':a.status,'reason':a.reason,'activity':a.activity,'evidence':evidence,'observed_model':a.model,'actor_id':a.actor})
        print(json.dumps(result,ensure_ascii=False));return 0
    except (ValueError,OSError,TypeError,KeyError,AttributeError) as exc:
        if a.action=='hook':
            print('NOTICE: Aikya execution metadata unavailable; existing gates remain authoritative.',file=sys.stderr);return 0
        p.exit(2,str(exc)+'\n')


def emit_engine_event(root,engine,action,result,session_id=None):
    """A recorder reports only its own operation. It never certifies tests or approves SDD."""
    from aikya.middleware.flow_bridge import context as flow_context
    context=flow_context(root,session_id or os.environ.get('CLAUDE_SESSION_ID','local'))
    try:
        active=state.read_active(context)
        if not active or active['status'] in state.TERMINAL:return
        context['run_id']=active['run_id']
        if action in ('new','clarify','plan','tasks','approve','reconcile'):
            state.record_event(context,{'phase':'plan','status':'waiting','reason':engine.upper()+' '+action+' recorded; next authorization or semantic phase transition is explicit','source':engine+'-recorder','actor_id':'local-python'})
        elif action=='progress':
            state.record_event(context,{'phase':'implement','status':'running','activity':engine.upper()+' task outcome recorded; verification is separate','source':engine+'-recorder','actor_id':'local-python'})
    except (ValueError,OSError,TypeError,KeyError):pass

if __name__=='__main__':raise SystemExit(main())
