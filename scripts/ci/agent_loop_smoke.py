#!/usr/bin/env python3
"""Explicit live SDK acceptance on a temporary synthetic project, never production."""
from __future__ import annotations
import argparse,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--live',action='store_true');p.add_argument('--approved',action='store_true');p.add_argument('--max-cost-usd',type=float,required=True);p.add_argument('--timeout-seconds',type=int,default=120);p.add_argument('--output',type=Path);p.add_argument('--approve-configured-hooks',action='store_true',help='Only after separately reviewing existing user/project SDK hooks')
    a=p.parse_args(argv)
    if not a.live or not a.approved:p.error('Both --live and --approved are required; there is no automatic model invocation')
    if a.output and (a.output.exists() or a.output.is_symlink() or not a.output.parent.is_dir()):p.error('Report destination must be a new file in an existing directory')
    from aikya.core.runtime import ProcessRuntime
    from aikya.core.loop import run,validated
    from aikya.workflows import odd as odd_engine
    runtime=ProcessRuntime()
    if not runtime.available():print(json.dumps({'status':'blocked','reason':'optional_sdk_missing'}));return 4
    with tempfile.TemporaryDirectory(prefix='aikya-live-loop-') as tmp:
        root=Path(tmp);(root/'.harness').mkdir();(root/'.harness/project-profile.json').write_text(json.dumps({'decisions':{'methodology':'odd','project_type':'development'}}))
        (root/'src').mkdir();(root/'src/value.py').write_text('VALUE = 0\n')
        odd_engine.prepare_feature(root,'value',{'title':'Controlled SDK smoke','objective':'Set VALUE to one in the approved fixture only.','acceptance':['The file contains exactly VALUE = 1.'],'tasks':[{'id':'TASK-001','description':'Change src/value.py to contain VALUE = 1 and a trailing newline. Do not use any other tool or file.','acceptance':['AC-01'],'depends_on':[],'files':['src/value.py'],'checks':['literal value and scoped AST check']}]},approved=True)
        checks=[{'name':'value','phase':'validate','argv':[sys.executable,'-c',"from pathlib import Path;assert Path('src/value.py').read_text()=='VALUE = 1\\n'"],'timeout_seconds':5},
                {'name':'scoped-ast','phase':'security','argv':[sys.executable,'-c',"import ast;from pathlib import Path;t=ast.parse(Path('src/value.py').read_text());assert all(not isinstance(n,(ast.Import,ast.ImportFrom,ast.Call)) for n in ast.walk(t))"],'timeout_seconds':5}]
        config={'schema':1,'command':'aikya-feature','work_id':'value','task_id':'TASK-001','files':['src/value.py'],'checks':checks,'max_turns':8,'timeout_seconds':a.timeout_seconds,'max_cost_usd':a.max_cost_usd,'hooks_approved':a.approve_configured_hooks}
        # Existing SDK configuration is not implicitly approved by a test flag.
        # If hooks are configured, the ordinary runtime preflight reports them.
        try:validated(root,config);result=run(root,config,runtime,approved=True)
        except (ValueError,OSError) as exc:print(json.dumps({'status':'blocked','reason':str(exc),'live':True}));return 4
        report={k:result[k] for k in ('status','reason','iteration','cost_usd','cost_known','tokens_known','token_totals') if k in result};report.update(live=True,runtime='claude-agent-sdk')
        if a.output:
            if a.output.exists() or a.output.is_symlink():raise ValueError('Smoke report destination must not already exist')
            a.output.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2));return 0 if report['status']=='completed' else 4
if __name__=='__main__':raise SystemExit(main())
