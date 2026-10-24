"""Real temporary projects and a bounded local subprocess, never an LLM mock."""
import json,os,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def project(base,method='odd',kind='development',locale='en'):
 root=Path(base)/'project';root.mkdir()
 profile=root/'.harness/project-profile.json';profile.parent.mkdir();profile.write_text(json.dumps({'decisions':{'methodology':method,'project_type':kind}}))
 policy=root/'.aikya/docs-policy.json';policy.parent.mkdir();policy.write_text(json.dumps({'schema_version':1,'language':locale}))
 (root/'src').mkdir();(root/'src/value.py').write_text('VALUE = 0\n')
 if method=='odd':
  from aikya.workflows import odd as odd_engine
  odd_engine.prepare_feature(root,'value',{'title':'Value','objective':'Set the fixture value.','acceptance':['Value equals one.'],'tasks':[{'id':'TASK-001','description':'Set value','acceptance':['AC-01'],'depends_on':[],'files':['src/value.py'],'checks':['check value']}]},approved=True)
 return root

def config():
 return {'schema':1,'command':'aikya-feature','work_id':'value','task_id':'TASK-001','files':['src/value.py'],'context_files':[],
         'max_turns':4,'timeout_seconds':20,'max_cost_usd':0.05,
         'checks':[{'name':'value','phase':'validate','argv':[sys.executable,'-c',"from pathlib import Path; assert 'VALUE = 1' in Path('src/value.py').read_text()"],'timeout_seconds':3},
                   {'name':'policy','phase':'security','argv':[sys.executable,'-c','raise SystemExit(0)'],'timeout_seconds':3}]}

def runtime(mode='write'):
 from aikya.core import runtime as agent_runtime
 return agent_runtime.ProcessRuntime(command=[sys.executable,str(ROOT/'tests/fixtures/agent-loop/worker.py')],env={'AIKYA_FIXTURE_MODE':mode})
