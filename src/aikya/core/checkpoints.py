"""Durable, bounded loop checkpoints. Conversation storage belongs to the runtime."""
from __future__ import annotations
import copy,hashlib,json,math,re,time,uuid
from pathlib import Path
from aikya.documentation.layout import index_paths,stamp,update_index
from aikya.documentation.language import resolve


def sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def safe_file(root,value,*,write=False):
    root=Path(root).absolute()
    if not isinstance(value,str) or not value or len(value)>240 or '\\' in value or Path(value).is_absolute() or any(p in ('','..','.') for p in value.split('/')):raise ValueError('Unsafe project path')
    parts=value.lower().split('/')
    if any(p=='.git' or p.startswith('.env') or p in ('.ssh','.aws','secrets','credentials') or p.startswith('credentials.') for p in parts):raise ValueError('Secret/control path is not allowed')
    if write and (parts[0] in ('.harness','.aikya','.claude') or value=='CLAUDE.md' or value.startswith(('aikya/docs/','aikya/scripts/'))):raise ValueError('Model cannot edit Aikya control files')
    path=root/value
    if any(p.is_symlink() for p in (path,*path.parents) if p==root or root in p.parents) or not path.resolve().is_relative_to(root.resolve()):raise ValueError('Symlinked or escaped project path')
    if path.exists() and not path.is_file():raise ValueError('Expected a regular file')
    return path


def fingerprint(path):
    if not path.exists():return None
    if path.is_symlink() or not path.is_file():raise ValueError('Expected a regular file')
    if path.stat().st_size>10_000_000:raise ValueError('File exceeds the loop inspection limit')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path,data):
    from aikya.storage import atomic_write
    raw=data if isinstance(data,str) else json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    if len(raw.encode())>2_000_000:raise ValueError('Oversized checkpoint')
    atomic_write(path,raw)


def folder(root,run_id):
    if not isinstance(run_id,str) or not re.fullmatch('[a-f0-9]{32}',run_id):raise ValueError('Invalid loop run ID')
    target=Path(root)/'aikya/docs/loops'/run_id
    safe_file(root,'aikya/docs/loops/'+run_id+'/state.json')
    return target


def identity(root):
    root=Path(root).resolve()
    # A changed root/worktree cannot silently inherit authorization from a copy.
    git=root/'.git';git_identity=fingerprint(git) if git.is_file() else str(git.resolve())
    return sha({'root':str(root),'git':git_identity})


def _account(data,result):
    ident=result.get('id');session=result.get('session_id');cost=result.get('cost_usd')
    if not isinstance(ident,str) or not re.fullmatch('[a-zA-Z0-9_-]{1,100}',ident) or not isinstance(session,str) or not re.fullmatch('[a-zA-Z0-9_-]{1,100}',session):raise ValueError('Invalid runtime result identity')
    usage=result.get('model_usage')
    counts=('inputTokens','outputTokens','cacheReadInputTokens','cacheCreationInputTokens')
    if usage is not None:
        if not isinstance(usage,dict) or len(usage)>10:raise ValueError('Invalid per-model usage')
        clean={}
        for model,values in usage.items():
            if not isinstance(model,str) or not 0<len(model)<=120 or not isinstance(values,dict) or any(type(values.get(k)) is not int or values[k]<0 for k in counts):raise ValueError('Invalid per-model usage')
            clean[model]={k:values[k] for k in counts}
        usage=clean
    record={'session_id':session,'cost_usd':cost,'model_usage':usage}
    if ident in data['results']:
        if data['results'][ident]!=record:raise ValueError('Conflicting duplicate usage result')
        return
    data.setdefault('token_totals',{k:0 for k in counts});data.setdefault('token_sessions',{});data.setdefault('tokens_known',True)
    if usage is None:data['tokens_known']=False
    else:
        previous_usage=data['token_sessions'].get(session,{})
        for model,values in usage.items():
            before=previous_usage.get(model,{k:0 for k in counts})
            if any(values[k]<before[k] for k in counts):raise ValueError('Session token counts decreased')
            for k in counts:data['token_totals'][k]+=values[k]-before[k]
        data['token_sessions'][session]=usage
    if cost is None:data['cost_known']=False;data['results'][ident]=record;return
    if type(cost) not in (int,float) or not math.isfinite(cost) or cost<0:raise ValueError('Invalid runtime cost estimate')
    previous=data['sessions'].get(session,0)
    if cost<previous:raise ValueError('Session estimate decreased; reconcile accounting')
    data['cost_usd']=round(data['cost_usd']+cost-previous,10)
    data['sessions'][session]=cost;data['results'][ident]=record


def account(data,result):
    # A malformed provider message must not leave a half-updated durable ledger.
    draft=copy.deepcopy(data)
    _account(draft,result)
    data.clear();data.update(draft)


def create(root,config):
    return {'schema':1,'generated_by':'aikya-agent-loop','run_id':uuid.uuid4().hex,'identity':identity(root),'config':config,'config_hash':sha(config),'revision':0,'status':'running','reason':'','phase':'Explore','iteration':0,'stalled':0,'candidate_generation':0,'cost_usd':0.0,'cost_known':True,'sessions':{},'results':{},'token_totals':{k:0 for k in ('inputTokens','outputTokens','cacheReadInputTokens','cacheCreationInputTokens')},'token_sessions':{},'tokens_known':True,'elapsed_seconds':0.0,'pending':{},'runtime_session':None,'bindings':{},'files':{},'events':[],'summary_hash':None,'previous_summary_hash':None,'evidence_hash':None,'created_at':time.time()}


def load(root,run_id):
    path=folder(root,run_id)/'state.json'
    if not path.is_file() or path.stat().st_size>2_000_000:raise ValueError('Missing or oversized loop state')
    data=json.loads(path.read_text())
    keys=set(create(root,{}))
    if not isinstance(data,dict) or set(data)!=keys or data.get('schema')!=1 or data.get('generated_by')!='aikya-agent-loop' or data.get('run_id')!=run_id or data.get('identity')!=identity(root):raise ValueError('Invalid loop state or different checkout')
    if data['config_hash']!=sha(data['config']):raise ValueError('Modified loop configuration')
    if data['status'] not in ('running','waiting','blocked','interrupted','completed','failed') or data['phase'] not in ('Explore','Plan','Implement','Validate','Security','Review'):raise ValueError('Invalid loop status')
    for key in ('revision','iteration','stalled','candidate_generation'):
        if type(data[key]) is not int or data[key]<0:raise ValueError('Invalid loop counter')
    for key in ('elapsed_seconds','cost_usd'):
        if type(data[key]) not in (int,float) or not math.isfinite(data[key]) or data[key]<0:raise ValueError('Invalid accumulated budget')
    if type(data['cost_known']) is not bool or any(not isinstance(data[k],dict) for k in ('pending','bindings','files','sessions','results','token_totals','token_sessions')) or not isinstance(data['events'],list) or len(data['events'])>200:raise ValueError('Invalid checkpoint fields')
    ledger={'cost_usd':0.0,'cost_known':True,'sessions':{},'results':{},'token_totals':{k:0 for k in ('inputTokens','outputTokens','cacheReadInputTokens','cacheCreationInputTokens')},'token_sessions':{},'tokens_known':True}
    for ident,record in data['results'].items():account(ledger,{'id':ident,**record})
    if any(ledger[k]!=data[k] for k in ('cost_usd','cost_known','sessions','token_totals','token_sessions','tokens_known')):raise ValueError('Inconsistent usage ledger')
    if data['evidence_hash'] is not None and data['evidence_hash']!=fingerprint(folder(root,run_id)/'evidence.json'):raise ValueError('Modified loop evidence')
    summary=folder(root,run_id)/'summary.md'
    if fingerprint(summary) not in (data['summary_hash'],data['previous_summary_hash']):raise ValueError('Customized loop summary; review before resume')
    return data


def save(root,data):
    target=folder(root,data['run_id']);index_paths(Path(root))
    previous=target/'summary.md'
    current_summary=fingerprint(previous)
    if current_summary not in (data['summary_hash'],data['previous_summary_hash']):raise ValueError('Customized loop summary is protected')
    es=resolve(Path(root))=='es'
    body=stamp(('# Ejecución del agent loop' if es else '# Agent loop execution')+'\n\n'+
        '\n'.join(f'- {key}: {data[key]}' for key in ('run_id','status','phase','reason','iteration','candidate_generation','cost_usd','cost_known','tokens_known','token_totals','elapsed_seconds'))+
        '\n\n'+('Estimación local de API; no es facturación ni cuota del proveedor.' if es else 'Local API estimate; not billing or provider quota.')+'\n\n'+
        '\n'.join('- '+e['phase']+': '+e['status'] for e in data['events']))
    data['previous_summary_hash']=current_summary;data['summary_hash']=hashlib.sha256(body.encode()).hexdigest();data['revision']+=1
    # State is authoritative. A cut before its projection is written is recoverable
    # only when the remaining projection still matches the prior managed hash.
    atomic(target/'state.json',data);atomic(previous,body);update_index(Path(root))
    return data
