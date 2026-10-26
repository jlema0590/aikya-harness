#!/usr/bin/env python3
"""Optional Claude Code task rows. A model belongs only to its observed actor."""
from __future__ import annotations
import json,sys
sys.dont_write_bytecode=True
from aikya.middleware.metrics import safe_text,number

def render_actor_rows(payload:dict,snapshot:dict)->list[dict]:
    tasks=payload.get('tasks',[]) if isinstance(payload,dict) else []
    if not isinstance(tasks,list):return []
    result=[]
    for task in tasks[:40]:
        if not isinstance(task,dict):continue
        model=task.get('model')
        if isinstance(model,dict):model=model.get('id')
        result.append({'id':safe_text(task.get('id')),'actor':safe_text(task.get('agentType')) or 'agent','status':safe_text(task.get('status')) or 'N/D','model':safe_text(model),'tokens':number(task.get('tokenCount')),'source':'runtime-task'})
    return result

def main():
    try:
        payload=json.load(sys.stdin);rows=render_actor_rows(payload,{})
        width=payload.get('columns',120);width=max(20,min(width,500)) if type(width) is int else 120
        for row in rows:
            if not row['id']:continue
            body=' · '.join((row['actor'],row['status'],row['model'] or 'N/D','Tokens: '+str(row['tokens']) if row['tokens'] is not None else 'Tokens: N/D'))
            print(json.dumps({'id':row['id'],'content':body[:width]}))
    except (ValueError,OSError,TypeError):pass
    return 0
if __name__=='__main__':raise SystemExit(main())
