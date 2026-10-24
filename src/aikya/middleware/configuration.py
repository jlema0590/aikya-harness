"""Merge visibility configuration without replacing user commands or permissions."""
from __future__ import annotations
import json
EVENTS={'UserPromptSubmit':None,'PreToolUse':'Skill','PostToolUseFailure':None,'SubagentStart':None,'SubagentStop':None,'StopFailure':None,'SessionEnd':None}

def merge_visibility(settings:dict,observer_command:str,status_command:str,subagent_command:str|None=None):
    if not isinstance(settings,dict) or not isinstance(settings.get('hooks',{}),dict):raise ValueError('Invalid settings; preserve and review manually')
    merged=json.loads(json.dumps(settings));proposals={};hooks=merged.setdefault('hooks',{})
    for name,matcher in EVENTS.items():
        groups=hooks.setdefault(name,[])
        if not isinstance(groups,list):raise ValueError('Invalid hook groups; preserve and review manually')
        # An existing local/global observer can share the cache. Avoid duplicate registrations.
        if any('execution_observer.py' in str(h.get('command','')) or 'execution_status.py' in str(h.get('command','')) for group in groups if isinstance(group,dict) for h in group.get('hooks',[]) if isinstance(h,dict)):continue
        group={'hooks':[dict(observer_command) if isinstance(observer_command,dict) else {'type':'command','command':observer_command,'timeout':5}]}
        if matcher:group['matcher']=matcher
        groups.append(group)
    for key,command in (('statusLine',status_command),('subagentStatusLine',subagent_command)):
        if not command:continue
        proposed={'type':'command','command':command}
        if key not in merged:merged[key]=proposed
        elif merged[key]!=proposed:proposals[key]=proposed
    return merged,proposals

def register_visibility(settings,observer_command,status_command,logs,proposal_path,subagent_command=None):
    from pathlib import Path
    settings=Path(settings);proposal_path=Path(proposal_path)
    if any(p.is_symlink() for p in (settings,*settings.parents,proposal_path,*proposal_path.parents)):
        logs.append('NOTICE: visibility configuration requires symlink review');return
    try:
        current=json.loads(settings.read_text(encoding='utf8')) if settings.exists() else {}
        updated,proposals=merge_visibility(current,observer_command,status_command,subagent_command)
    except (ValueError,OSError,TypeError):
        logs.append('NOTICE: custom configuration preserved; visibility requires manual review');return
    if updated!=current:
        settings.parent.mkdir(parents=True,exist_ok=True);settings.write_text(json.dumps(updated,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        logs.append('REGISTERED Aikya execution visibility: '+str(settings))
    if proposals:
        if not proposal_path.exists():
            proposal_path.parent.mkdir(parents=True,exist_ok=True);proposal_path.write_text(json.dumps(proposals,indent=2)+'\n',encoding='utf8')
        logs.append('NEEDS_REVIEW: custom status line preserved; proposed values: '+str(proposal_path))
