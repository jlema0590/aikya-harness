"""Compact local tool responses; failure status and omissions remain explicit."""
import contextlib
import io
import json


def compact(result, *, exit_code=0):
    counts={}; blockers=[]; references=[]
    def walk(value, key=''):
        if isinstance(value,dict):
            for name,item in value.items():walk(item,name)
        elif isinstance(value,list):
            counts[key]=counts.get(key,0)+len(value)
            if key in ('errors','blockers','conflicts','missing','warnings'):
                blockers.extend(str(x) for x in value)
            else:
                for item in value:
                    if isinstance(item,(dict,list)):walk(item,key)
        elif key in ('path','report_path','state_path','html_path') and isinstance(value,str):
            references.append(value)
    walk(result)
    status=result.get('status',result.get('ready')) if isinstance(result,dict) else None
    summary={'status':status if status is not None else ('ok' if exit_code==0 else 'blocked'),
             'exit_code':exit_code,'counts':counts,'blockers':list(dict.fromkeys(blockers)),
             'references':list(dict.fromkeys(references))[:8],
             'omitted_count':sum(counts.values()),
             'detail':'Use the same command without --summary for complete local details; no extra model call is needed.'}
    # Never truncate a blocking reason to meet the preferred response size.
    if len(json.dumps(summary,ensure_ascii=False))>2000:summary['summary_budget_exceeded']=True
    return summary


def run_compact(callback, argv):
    output=io.StringIO()
    with contextlib.redirect_stdout(output):code=callback(argv)
    text=output.getvalue();decoder=json.JSONDecoder();values=[];position=0
    while position<len(text):
        if text[position] not in '{[':position+=1;continue
        try:
            value,end=decoder.raw_decode(text,position);values.append(value);position=end
        except ValueError:position+=1
    result=values[-1] if values else {}
    summary=compact(result,exit_code=code)
    print(json.dumps(summary,ensure_ascii=False))
    return code
