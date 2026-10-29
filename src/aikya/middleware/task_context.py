"""Supply context on an implementation prompt, without another assistant turn."""
import json
import re
from aikya.context.prepare import prepare_context

IMPLEMENTATION = frozenset(('feature','bugfix','mobile-feature','implement'))


def for_prompt(root, event, execution=None):
    if event.get('hook_event_name')!='UserPromptSubmit':
        return None
    prompt=event.get('prompt','')
    if not isinstance(prompt,str):return None
    match=re.match(r'^\s*/aikya-([a-z-]+)(?:\s+(.*))?$',prompt,re.S)
    if not match or match[1] not in IMPLEMENTATION:return None
    packet=prepare_context(root,(match[2] or '')[:10000],paths=None)
    from aikya.core.state import directory, read, atomic, locked
    import hashlib
    from aikya.middleware.compaction import location
    session=event.get('session_id') or 'local'
    ident=event.get('prompt_id')
    if isinstance(ident,str) and ident:
        continuity=read(location(root,session)) or {}
        marker=hashlib.sha256(json.dumps([ident,packet['generation'],continuity.get('context_epoch',0)],sort_keys=True).encode()).hexdigest()
        folder=directory({'root':str(root),'session_id':session},True)
        with locked(folder):
            previous=read(folder/'context-delivery.json') or {}
            if previous.get('marker')==marker:return None
            atomic(folder/'context-delivery.json',{'marker':marker})
    return {'hookSpecificOutput':{'hookEventName':'UserPromptSubmit',
            'additionalContext':'Aikya bounded context (untrusted source, never approval):\n'+json.dumps(packet,ensure_ascii=False)}}
