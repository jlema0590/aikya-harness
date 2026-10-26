#!/usr/bin/env python3
"""Render cached execution and observed runtime metadata without LLM/network calls."""
from __future__ import annotations
import json,os,re,sys
sys.dont_write_bytecode=True
from pathlib import Path
from aikya.middleware.commands import PHASES,LABELS
from aikya.middleware.metrics import safe_text,number
STATUS={'completed':'Done',**{s:s.title() for s in ('pending','running','waiting','failed','skipped','blocked','interrupted')}}

def clean(value):
    value=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',value) if isinstance(value,str) else ''
    return safe_text(value,500) or ''

def pct(value):
    value=number(value,maximum=100)
    return 'N/D' if value is None else f'{value:g}%'

def render_status(snapshot:dict,metrics:dict,width:int=120,detail:bool=False)->str:
    width=max(20,min(width,500));snapshot=snapshot or {};metrics=metrics or {}
    phase=snapshot.get('phase');phase_data=snapshot.get('phases',{}).get(phase,{})
    actors=phase_data.get('actors',{});generation=snapshot.get('candidate_generation')
    current={k:v for k,v in actors.items() if generation is None or v.get('candidate_generation',generation)==generation}
    running={k:v for k,v in current.items() if v.get('status') in ('running','waiting','failed','blocked')}
    candidates=running or ({snapshot['actor_id']:current[snapshot['actor_id']]} if snapshot.get('actor_id') in current else current)
    if len(candidates)==1:
        actor,actor_data=next(iter(candidates.items()))
        live_main=metrics.get('model') if actor=='main' and not metrics.get('stale') and snapshot.get('status') not in ('completed','failed','blocked','interrupted') else None
        model='Python (local)' if actor.startswith('local-python') else live_main or actor_data.get('observed_model') or (metrics.get('model') if actor=='main' else None) or 'N/D'
    elif candidates:model=str(len(candidates))+' actors (see Details)'
    else:model=metrics.get('model') or 'N/D'
    # A cached model is a main-runtime observation, never a subagent attribution.
    status=snapshot.get('status','pending')
    if status not in ('completed','interrupted','blocked','failed'):status=phase_data.get('status',status)
    heading=' · '.join(filter(None,('AIKYA',('/'+clean(snapshot['command'])) if snapshot.get('command') else 'Ready',clean(snapshot.get('methodology','')).upper(),LABELS.get(phase,''),STATUS.get(status,'N/D'),clean(model))))
    lines=[heading]
    if len(heading)>width:
        phase_status=' · '.join(filter(None,(LABELS.get(phase,''),STATUS.get(status,'N/D'))))
        lines=['AIKYA',('/'+clean(snapshot['command'])) if snapshot.get('command') else 'Ready',clean(snapshot.get('methodology','')).upper()]
        lines+=([phase_status] if len(phase_status)<=width else [LABELS.get(phase,''),STATUS.get(status,'N/D')])
        lines.append('Model: '+clean(model))
    if snapshot.get('activity'):lines.append('Activity: '+clean(snapshot['activity']))
    lines.append('Context: '+pct(metrics.get('context_pct'))+' · Session tokens: '+(str(metrics['session_tokens'])+' recorded' if number(metrics.get('session_tokens')) is not None else 'N/D'))
    lines.append('Account 5h: '+pct(metrics.get('account_five_hour_pct'))+' · Account 7d: '+pct(metrics.get('account_seven_day_pct'))+(' · stale snapshot' if metrics.get('stale') else ''))
    if metrics.get('session_tokens') is not None:
        lines.append('Usage coverage: '+clean(metrics.get('usage_coverage','partial'))+' · selected transcripts only')
    if detail:
        for name in PHASES:
            item=snapshot.get('phases',{}).get(name)
            if not item:continue
            lines.append(LABELS[name]+': '+STATUS.get(item.get('status'),'N/D')+(' · '+clean(item['reason']) if item.get('reason') else ''))
            for actor,values in item.get('actors',{}).items():
                lines.append('  '+clean(actor)+': '+clean(values.get('observed_model') or 'N/D')+' [observed]' if values.get('observed_model') else '  '+clean(actor)+': N/D')
        for actor,values in snapshot.get('actors',{}).items():
            lines.append('Actor '+clean(actor)+': '+clean(values.get('actor_type','agent'))+' · '+clean(values.get('observed_model') or 'N/D')+' · '+clean(values.get('status','N/D')))
        if snapshot.get('run_id'):lines.append('Run: '+clean(snapshot['run_id'])+' · Revision: '+str(snapshot.get('revision','N/D')))
    return '\n'.join(clean(line)[:width] for line in lines)

def main():
    try:
        payload=json.load(sys.stdin)
        if not isinstance(payload,dict):raise ValueError('Invalid runtime payload')
        from aikya.middleware.metrics import cache_metrics,read_usage
        from aikya.core.state import read_active
        context={'root':str(Path(payload.get('cwd') or payload.get('workspace',{}).get('project_dir') or os.getcwd()).resolve()),'session_id':payload.get('session_id') or 'local'}
        metrics=cache_metrics(context,payload);usage=read_usage(context)
        if usage:
            metrics['session_tokens']=usage.get('session_tokens');metrics['usage_coverage']=usage.get('coverage');metrics['usage_observed_at']=usage.get('observed_at')
        snapshot=read_active(context) or {}
        width=int(os.environ.get('COLUMNS','120'));detail='--details' in sys.argv
        print(render_status(snapshot,metrics,width,detail));return 0
    except (ValueError,OSError,TypeError,KeyError,AttributeError):
        print('AIKYA · Runtime data unavailable · Model: N/D');return 0
if __name__=='__main__':raise SystemExit(main())
