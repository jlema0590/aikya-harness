"""Optional Claude SDK worker with scoped tools and a bounded subprocess protocol."""
from __future__ import annotations
from aikya.core.permissions import settings_paths,settings_fingerprints,tool_path,tool_allowed
import importlib.util,json,os,signal,subprocess,sys,time,uuid
from pathlib import Path
from aikya.core.checkpoints import safe_file
from aikya.core.pipe_reader import PipeReader










class ProcessRuntime:
    def __init__(self,command=None,env=None):
        # A registered copy may not be installed in this interpreter. Pin the
        # child to the same package, ignoring project/PYTHONPATH import shadows.
        package_parent=str(Path(__file__).resolve().parents[2])
        bootstrap='import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module("aikya.core.runtime",run_name="__main__")'
        self.command=command or [sys.executable,'-I','-B','-c',bootstrap,package_parent,'worker']
        self.env=env or {};self.is_sdk=command is None
    def available(self):return not self.is_sdk or importlib.util.find_spec('claude_agent_sdk') is not None
    def execute(self,request,on_event,cancel=lambda:False):
        if not self.available():raise ValueError('optional_sdk_missing')
        env={**os.environ,**self.env,'AIKYA_AGENT_LOOP_CHILD':'1','PYTHONDONTWRITEBYTECODE':'1'}
        proc=subprocess.Popen(self.command,cwd=request['root'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env,start_new_session=os.name!='nt')
        reader=None
        limit=time.monotonic()+request['timeout_seconds'];buffer=b'';result=None
        try:
            reader=PipeReader(proc.stdout)
            proc.stdin.write((json.dumps(request)+'\n').encode());proc.stdin.flush()
            while True:
                if cancel():raise InterruptedError('cancelled')
                if time.monotonic()>=limit:raise TimeoutError('runtime_timeout')
                chunk=reader.read(min(0.05,max(0,limit-time.monotonic())))
                if chunk is None:
                    continue
                if not chunk:break
                buffer+=chunk
                if len(buffer)>131072:raise ValueError('oversized_runtime_message')
                while b'\n' in buffer:
                    line,buffer=buffer.split(b'\n',1);event=json.loads(line)
                    if not isinstance(event,dict):raise ValueError('invalid_runtime_event')
                    if event.get('type')=='result':
                        if result is not None:raise ValueError('duplicate_runtime_result')
                        result=event
                    else:
                        if result is not None:raise ValueError('event_after_result')
                        on_event(event)
                        if event.get('type')=='effect_intent':
                            proc.stdin.write((json.dumps({'ack':event['id']})+'\n').encode());proc.stdin.flush()
            proc.wait(timeout=max(0.05,limit-time.monotonic()))
            if proc.returncode or result is None or buffer.strip():raise ValueError('incomplete_runtime_result')
            return result
        finally:
            if os.name!='nt':
                try:os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError:pass
            elif proc.poll() is None:proc.kill()
            proc.wait()
            proc.stdin.close();proc.stdout.close()
            if reader is not None:reader.close()


def sdk_options(request,emit,ack):
    # Lazy import: normal Aikya commands never require the optional SDK.
    from claude_agent_sdk import ClaudeAgentOptions,HookMatcher,PermissionResultDeny
    async def before(data,tool_id,context):
        tool=data.get('tool_name');inputs=data.get('tool_input',{})
        # SDK-owned JSON formatter has no file/process effects. Its output is
        # validated again by the controller and can never complete a task alone.
        if tool=='StructuredOutput':return {}
        if not tool_allowed(request,tool,inputs):
            emit({'type':'permission_required'})
            return {'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'Outside the explicitly approved loop scope'}}
        if tool in ('Edit','Write'):
            ident=tool_id or data.get('tool_use_id') or uuid.uuid4().hex
            relative=tool_path(request,inputs['file_path'])
            emit({'type':'effect_intent','id':ident,'tool':tool,'path':relative})
            await ack(ident)
        return {}
    async def after(data,tool_id,context):
        if data.get('tool_name') in ('Edit','Write'):emit({'type':'effect_result','id':tool_id or data.get('tool_use_id')})
        return {}
    async def permission(tool,inputs,context):
        emit({'type':'permission_required'})
        return PermissionResultDeny(message='A separate permission decision is needed',interrupt=True)
    schema={'type':'object','properties':{'status':{'type':'string','enum':['done','needs_input']},'approved':{'type':'boolean'}},'required':['status','approved'],'additionalProperties':False}
    if request['phase']=='extract':
        item={'type':'object','properties':{'kind':{'type':'string','enum':['user','feedback','project','reference']},'text':{'type':'string','maxLength':8000},'source':{'type':'string'},'ttl_days':{'type':'integer','minimum':1,'maximum':365}},'required':['kind','text','source','ttl_days'],'additionalProperties':False}
        schema={'type':'object','properties':{'candidates':{'type':'array','maxItems':3,'items':item}},'required':['candidates'],'additionalProperties':False}
    tools=['Read','Edit','Write'] if request['phase']=='implement' else ['Read']
    return ClaudeAgentOptions(cwd=request['root'],tools=tools,allowed_tools=tools+['StructuredOutput'],
        permission_mode='default',can_use_tool=permission,
        setting_sources=['user','project','local'],strict_mcp_config=True,mcp_servers={},skills=[],
        hooks={'PreToolUse':[HookMatcher(hooks=[before])],'PostToolUse':[HookMatcher(hooks=[after])]},
        max_turns=request['max_turns'],max_budget_usd=request['remaining_cost_usd'],resume=request.get('session_id'),
        output_format={'type':'json_schema','schema':schema},
        system_prompt={'type':'preset','preset':'claude_code'},env={'AIKYA_AGENT_LOOP_CHILD':'1'},stderr=lambda line:None)


async def sdk_worker(request):
    import asyncio
    from claude_agent_sdk import query,AssistantMessage,ResultMessage
    def emit(data):print(json.dumps(data),flush=True)
    async def ack(ident):
        raw=await asyncio.to_thread(sys.stdin.readline)
        if json.loads(raw).get('ack')!=ident:raise ValueError('Missing durable effect acknowledgement')
    model=None;options=sdk_options(request,emit,ack)
    async for message in query(prompt=request['prompt'],options=options):
        if isinstance(message,AssistantMessage):
            model=message.model;emit({'type':'model','model':model})
        elif isinstance(message,ResultMessage):
            terminal=getattr(message,'terminal_reason',None)
            valid=not message.is_error and message.subtype=='success' and terminal in (None,'completed') and getattr(message,'stop_reason',None)!='refusal'
            output=message.structured_output if valid else {'status':'needs_input','approved':False}
            emit({'type':'result','id':message.uuid or uuid.uuid4().hex,'session_id':message.session_id,
                  'cost_usd':message.total_cost_usd,'model_usage':getattr(message,'model_usage',None),'model':model,'output':output,'error':not valid})


def main():
    import asyncio
    if sys.argv[1:] == ['check']:
        if not ProcessRuntime().available():print(json.dumps({'available':False,'reason':'optional_sdk_missing'}));return 4
        import importlib.metadata
        print(json.dumps({'available':True,'sdk_version':importlib.metadata.version('claude-agent-sdk')}));return 0
    if sys.argv[1:]!=['worker']:return 2
    request=json.loads(sys.stdin.readline())
    try:asyncio.run(sdk_worker(request));return 0
    except Exception:
        # Error details may include provider prompts or credentials. Do not persist them.
        return 2
if __name__=='__main__':raise SystemExit(main())
