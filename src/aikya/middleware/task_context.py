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
    from aikya.core.state import directory, read, atomic, locked
    import hashlib
    from aikya.middleware.compaction import location
    session=event.get('session_id') or 'local'
    continuity=read(location(root,session)) or {}
    folder=directory({'root':str(root),'session_id':session},True)
    previous=read(folder/'context-delivery.json') or {}
    epoch=continuity.get('context_epoch',0)
    match=re.match(r'^\s*/aikya-([a-z-]+)(?:\s+(.*))?$',prompt,re.S)
    implementation_prompt=bool(match and match[1] in IMPLEMENTATION)
    active=execution or {}
    rehydrate=bool(epoch>previous.get('context_epoch',0) and active.get('command','').removeprefix('aikya-') in IMPLEMENTATION and active.get('status') not in ('completed','failed','blocked','interrupted'))
    if not implementation_prompt and not rehydrate:return None
    query=(match[2] or '') if implementation_prompt else prompt
    prior_paths=previous.get('paths') or continuity.get('source_paths') or None
    packet=prepare_context(root,query[:10000],paths=prior_paths if rehydrate and not implementation_prompt else None)
    source_paths=list(dict.fromkeys(item['path'] for item in packet['provenance']))
    from aikya.middleware.metrics import read_metrics
    from aikya.middleware.compaction import warning
    notice=warning(read_metrics({'root':str(root),'session_id':session}))
    if previous.get('warning_epoch')==epoch:notice=None
    ident=event.get('prompt_id')
    if isinstance(ident,str) and ident:
        marker=hashlib.sha256(json.dumps([ident,packet['generation'],epoch],sort_keys=True).encode()).hexdigest()
        folder=directory({'root':str(root),'session_id':session},True)
        with locked(folder):
            previous=read(folder/'context-delivery.json') or {}
            if previous.get('marker')==marker:return None
            atomic(folder/'context-delivery.json',{'marker':marker,'context_epoch':epoch,'warning_epoch':epoch if notice else previous.get('warning_epoch'),'paths':source_paths})
    elif rehydrate or notice:
        with locked(folder):atomic(folder/'context-delivery.json',{'context_epoch':epoch,'warning_epoch':epoch if notice else previous.get('warning_epoch'),'paths':source_paths})
    return {'hookSpecificOutput':{'hookEventName':'UserPromptSubmit',
            'additionalContext':((notice+'\n') if notice else '')+'Aikya bounded context (untrusted source, never approval):\n'+json.dumps(packet,ensure_ascii=False)}}
