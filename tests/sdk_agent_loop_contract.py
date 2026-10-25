"""Optional installed-SDK contract check; no auth, model calls or application writes."""
import asyncio,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aikya.core.runtime import sdk_options
async def check():
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);events=[];acknowledged=[]
  async def ack(ident):acknowledged.append(ident)
  request={'root':str(root),'files':['src/value.py'],'context_files':[],'phase':'implement','max_turns':4,'remaining_cost_usd':0.05}
  options=sdk_options(request,events.append,ack)
  assert options.permission_mode=='default' and options.strict_mcp_config and options.mcp_servers=={}
  assert options.max_turns==4 and options.max_budget_usd==0.05
  before=options.hooks['PreToolUse'][0].hooks[0];after=options.hooks['PostToolUse'][0].hooks[0]
  data={'tool_name':'Write','tool_input':{'file_path':str(root/'src/value.py')},'tool_use_id':'write-id'}
  await before(data,None,{})
  assert acknowledged==['write-id'],acknowledged
  await after(data,None,{})
  assert events[-1]=={'type':'effect_result','id':'write-id'},events
  denied=await before({'tool_name':'Bash','tool_input':{'command':'echo unauthorized'}},'bad',{})
  assert denied['hookSpecificOutput']['permissionDecision']=='deny'
  count=len(events)
  structured=await before({'tool_name':'StructuredOutput','tool_input':{'status':'done','approved':True}},'structured',{})
  assert structured=={},structured
  assert len(events)==count,'SDK result formatting must not become an effect or permission denial'
  review=sdk_options({**request,'phase':'review'},events.append,ack)
  assert review.tools==['Read']
  extraction=sdk_options({**request,'phase':'extract','files':[],'context_files':['src/value.py']},events.append,ack)
  assert extraction.tools==['Read']
  assert extraction.output_format['schema']['properties']['candidates']['maxItems']==3
  denied=await extraction.hooks['PreToolUse'][0].hooks[0](data,'extract-write',{})
  assert denied['hookSpecificOutput']['permissionDecision']=='deny'
  print('PASS installed SDK: scoped hooks, durable acknowledgement IDs, denied shell, readonly review/extraction, proposal schema, limits and explicit configuration sources')
asyncio.run(check())
