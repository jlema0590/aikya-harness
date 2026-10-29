"""Fresh bounded source packets shared by slash hooks, CLI and the task loop."""
import json
from pathlib import Path
from aikya.core.checkpoints import safe_file
from aikya.code_index.policy import project_root, load_policy, excluded, read_source, content_hash
from aikya.code_index.scan import inventory, ignored
from aikya.code_index.store import IndexStore
from aikya.code_index.sync import sync
from aikya.code_index.coverage import summarize
from .ranking import rank


def prepare_context(root, query, *, paths, max_chars=6000):
    root = project_root(root)
    if not isinstance(query, str) or len(query)>10000 or type(max_chars) is not int or not 512<=max_chars<=16000:
        raise ValueError('Invalid context query or packet budget (512–16000 chars)')
    if paths is not None and (not isinstance(paths,list) or len(paths)>100):
        raise ValueError('Explicit context scope must be a list of at most 100 files')
    for path in paths or []:
        safe_file(root,path)
    options = load_policy(root)
    packet = {'schema':1,'status':'available','generation':0,'context':[], 'provenance':[],
              'coverage':{},'diagnostics':[],'omitted_count':0}
    entries = []
    if options.enabled:
        try:
            sync(root)
            snapshot = IndexStore(root).read_snapshot()
            packet.update(generation=snapshot.generation,status=snapshot.status,
                          coverage=summarize(snapshot.files,snapshot.symbols))
            entries = list(snapshot.symbols)
            entries.extend({'path':f['path'],'name':Path(f['path']).name,'start_line':1,'end_line':20,
                            'file_sha256':f['sha256'],'kind':'file'} for f in snapshot.files if f['status']=='file_only')
        except (ValueError,OSError):
            packet['status']='fallback'
            packet['diagnostics'].append('index_unavailable')
    else:
        packet['diagnostics'].append('index_disabled')
    if not entries:
        # Disabled/missing index permits bounded direct reads, never another root.
        candidates = paths
        if candidates is None:
            candidates, diagnostics = inventory(root,options)
            packet['diagnostics'].extend(diagnostics[:4])
        entries = [{'path':p,'name':Path(p).name,'start_line':1,'end_line':20,'kind':'file'} for p in candidates]
        packet['diagnostics'].append('bounded_source_fallback')
    eligible = [(s, rank(s,query)) for s in entries if (paths is None or s['path'] in paths)
                and not excluded(s['path']) and (options.scope=='.' or s['path']==options.scope or s['path'].startswith(options.scope.rstrip('/')+'/'))]
    eligible.sort(key=lambda pair:pair[1])
    hidden = ignored(root,[s['path'] for s,_ in eligible])
    seen=set();read_bytes=0
    for symbol, ranking in eligible:
        path=symbol['path']
        if path in hidden or path in seen or (ranking[0]==0 and query.strip() and paths is None):
            continue
        seen.add(path)
        if len(packet['context'])>=8:
            packet['omitted_count']+=1;continue
        try:
            raw=read_source(root,path,options.max_file_bytes);read_bytes+=len(raw)
            if read_bytes>options.max_sync_bytes:raise ValueError('read_budget')
            digest=content_hash(raw)
            if symbol.get('file_sha256',digest)!=digest:
                packet['diagnostics'].append('source_changed');continue
            start=symbol.get('start_line',1);end=min(symbol.get('end_line',start+19),start+19)
            snippet='\n'.join(raw.decode('utf8').splitlines()[start-1:end])[:2000]
        except (OSError,ValueError,UnicodeError):
            packet['diagnostics'].append('source_unavailable');continue
        packet['context'].append({'path':path,'start_line':start,'end_line':end,'text':snippet})
        packet['provenance'].append({'path':path,'sha256':digest,'kind':symbol['kind']})
        if len(json.dumps(packet,ensure_ascii=False))>max_chars:
            packet['context'].pop();packet['provenance'].pop();packet['omitted_count']+=1
    # Budget includes metadata and JSON serialization, not just snippets.
    if len(json.dumps(packet,ensure_ascii=False))>max_chars:
        packet['coverage']={'status':'omitted_for_budget'}
    packet['diagnostics']=list(dict.fromkeys(packet['diagnostics']))[:6]
    if len(json.dumps(packet,ensure_ascii=False))>max_chars:
        packet['context']=[];packet['provenance']=[];packet['status']='budget_exhausted'
    return packet
