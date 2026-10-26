"""Normalize observed runtime fields; never infer account quotas from token logs."""
from __future__ import annotations
from datetime import datetime,timezone
import math,time
from pathlib import Path

def number(value,minimum=0,maximum=None):
    return value if type(value) in (int,float) and math.isfinite(value) and value>=minimum and (maximum is None or value<=maximum) else None

def safe_text(value,limit=120):
    return ''.join(c for c in value if c.isprintable())[:limit] if isinstance(value,str) and value.strip() else None

def normalize_runtime_payload(payload: dict,now=None) -> dict:
    if not isinstance(payload,dict):raise ValueError('Runtime payload must be an object')
    now=time.time() if now is None else now
    model=payload.get('model') if isinstance(payload.get('model'),dict) else {}
    ctx=payload.get('context_window') if isinstance(payload.get('context_window'),dict) else {}
    limits=payload.get('rate_limits') if isinstance(payload.get('rate_limits'),dict) else {}
    result={'source':'claude-statusline','observed_at':now,'model':safe_text(model.get('id')),
            'model_display':safe_text(model.get('display_name')),'context_pct':number(ctx.get('used_percentage'),maximum=100),
            'context_size':number(ctx.get('context_window_size')),'session_tokens':None}
    for key,label in (('five_hour','account_five_hour'),('seven_day','account_seven_day')):
        bucket=limits.get(key) if isinstance(limits.get(key),dict) else {};reset=number(bucket.get('resets_at'))
        result[label+'_pct']=number(bucket.get('used_percentage'),maximum=100) if reset is not None and reset>now else None
        result[label+'_resets_at']=reset if reset is not None and reset>now else None
    return result

def resolve_actor_model(configured,observed):
    value=safe_text(observed)
    return {'configured':safe_text(configured),'observed':value,'source':'runtime' if value else 'unavailable'}

def instant(value):
    if isinstance(value,datetime):return value.astimezone(timezone.utc).timestamp() if value.tzinfo else value.replace(tzinfo=timezone.utc).timestamp()
    if type(value) in (int,float) and math.isfinite(value):return value
    if isinstance(value,str):
        try:
            parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
            return (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).timestamp()
        except ValueError:return None
    return None

def aggregate_usage(paths,start_utc=None,end_utc=None,session_id=None):
    from aikya.middleware.usage import summarize
    paths=list(map(Path,paths));start=instant(start_utc);end=instant(end_utc)
    if (start_utc is not None and start is None) or (end_utc is not None and end is None) or (start is not None and end is not None and start>=end):raise ValueError('Invalid usage interval')
    for path in paths:
        if not path.is_file() or any(p.is_symlink() for p in (path,*path.parents) if p not in (Path('/tmp'),Path('/var'))):raise ValueError('Usage paths must be explicitly authorized regular files')
    coverage={'missing_timestamps':0,'status':'recorded','scope':'explicit project transcript paths','missing_usage':0}
    def include(event,path):
        if session_id is not None and str(event.get('sessionId') or event.get('session_id') or path.stem)!=session_id:return False
        stamp=instant(event.get('timestamp'))
        if start is not None or end is not None:
            if stamp is None:coverage['missing_timestamps']+=1;return False
            if (start is not None and stamp<start) or (end is not None and stamp>=end):return False
        return True
    report=summarize(paths,event_filter=include)
    coverage['missing_usage']=report.get('usage_records_missing',0)
    if coverage['missing_timestamps'] or coverage['missing_usage']:coverage['status']='partial'
    report['coverage']=coverage;report['interval']={'start_utc':start_utc.isoformat() if isinstance(start_utc,datetime) else start_utc,'end_utc':end_utc.isoformat() if isinstance(end_utc,datetime) else end_utc}
    return report

def budget_percentage(consumed,budget):
    if number(consumed) is None:raise ValueError('Invalid consumed token count')
    if budget is None:return None
    if number(budget) is None or budget<=0:raise ValueError('Budget must be a positive explicit token limit')
    return round(consumed/budget*100,2)

def cache_metrics(context,payload,now=None):
    from aikya.core.state import directory,atomic,locked
    value=normalize_runtime_payload(payload,now);folder=directory(context,True)
    with locked(folder):atomic(folder/'metrics.json',value)
    return value

def read_metrics(context,max_age=60,now=None):
    from aikya.core.state import directory,read
    value=read(directory(context)/'metrics.json')
    if not value:return {}
    now=time.time() if now is None else now
    value['stale']=now-value.get('observed_at',0)>max_age
    for label in ('account_five_hour','account_seven_day'):
        reset=number(value.get(label+'_resets_at'))
        if reset is None or reset<=now:value[label+'_pct']=None
    return value


def cache_usage(context,report):
    """Cache only a caller-authorized session aggregate, separate from provider limits."""
    from aikya.core.state import directory,atomic,locked
    from aikya.middleware.usage import KEYS
    totals=report.get('totals',{});value={'session_tokens':sum(totals.get(k,0) for k in KEYS) if totals.get('calls',0)>0 else None,
        'totals':{k:totals.get(k,0) for k in KEYS},'observed_at':time.time(),'source':'explicit-session-transcripts',
        'coverage':report.get('coverage',{}).get('status','partial'),'scope':'selected recorded session; excludes unprovided subagent transcripts'}
    folder=directory(context,True)
    with locked(folder):atomic(folder/'usage.json',value)
    return value

def read_usage(context):
    from aikya.core.state import directory,read
    return read(directory(context)/'usage.json') or {}
