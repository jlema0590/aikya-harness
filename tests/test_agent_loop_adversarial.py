"""Hostile inputs and interruption windows against the actual local controller."""
import copy,json,math,os,subprocess,sys,tempfile,threading,time,unittest
from pathlib import Path
from agent_loop_support import ROOT,project,config,runtime
from aikya.core import loop as agent_loop; from aikya.core import checkpoints as state
class AdversarialLoopTests(unittest.TestCase):
 def test_numeric_and_structural_fuzz_inputs_never_start_an_executor(self):
  cases=[]
  for key in ('max_turns','timeout_seconds','max_cost_usd','max_iterations'):
   for value in (None,False,True,0,-1,'5',float('nan'),float('inf'),[],{}):cases.append({**config(),key:value})
  for key,value in (('files',[]),('files',['src/value.py','src/value.py']),('files',['src/../value.py']),('files',['.ENV']),('context_files',['/etc/passwd']),('checks',[]),('checks',[{'name':'bad'}]),('command','aikya-init'),('schema',True)):
   cases.append({**config(),key:value})
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp)
   for i,raw in enumerate(cases):
    with self.subTest(case=i):
     with self.assertRaises(ValueError):agent_loop.run(root,raw,runtime(),approved=True)
   self.assertFalse((root/'aikya/docs/loops').exists())
 def test_cancel_before_execution_and_elapsed_or_cost_budget_exhaustion_are_durable(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);first=agent_loop.run(root,config(),runtime(),approved=True,cancel=lambda:True)
   self.assertEqual('interrupted',first['status']);self.assertEqual(0,first['iteration'])
   second=agent_loop.run(root,config(),runtime(),approved=True,run_id=first['run_id'])
   self.assertEqual('completed',second['status'])
 def test_moved_symlinked_checkpoint_and_custom_summary_are_never_followed_or_replaced(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);result=agent_loop.run(root,{**config(),'max_iterations':1},runtime('claim'),approved=True)
   folder=root/'aikya/docs/loops'/result['run_id'];summary=folder/'summary.md';summary.write_text('Team custom report\n')
   with self.assertRaises(ValueError):state.load(root,result['run_id'])
   self.assertEqual('Team custom report\n',summary.read_text())
   backup=folder/'state.json';backup.unlink();outside=Path(tmp)/'outside.json';outside.write_text('{}');backup.symlink_to(outside)
   with self.assertRaises(ValueError):state.load(root,result['run_id'])
   self.assertEqual('{}',outside.read_text())
 def test_sdd_unapproved_work_cannot_run_and_loop_never_approves_stages(self):
  from aikya.workflows.sdd import engine as sdd
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp,method='sdd');spec={'id':'SPEC-001','title':'Fixture value','objective':'Set one','requirements':[{'id':'REQ-001','description':'Value equals one','acceptance':['Value is one']}],'nonfunctional':[],'questions':[]}
   sdd.initialize(root,spec);raw={**config(),'work_id':'SPEC-001','command':'aikya-implement'}
   before=(root/'aikya/docs/specs/development/SPEC-001/state.json').read_bytes()
   with self.assertRaises(ValueError):agent_loop.run(root,raw,runtime(),approved=True)
   self.assertEqual(before,(root/'aikya/docs/specs/development/SPEC-001/state.json').read_bytes())
 def test_check_changes_to_approvals_block_before_another_runtime_call(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);raw=config()
   raw['checks'][0]['argv']=[sys.executable,'-c',"import json;from pathlib import Path;p=Path('.harness/project-profile.json');v=json.loads(p.read_text());v['decisions']['methodology']='sdd';p.write_text(json.dumps(v))"]
   result=agent_loop.run(root,raw,runtime(),approved=True)
   self.assertEqual('approvals_changed',result['reason']);self.assertEqual(1,len(result['results']))
 def test_changed_candidate_during_review_cannot_complete_task(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);result=agent_loop.run(root,config(),runtime('stale'),approved=True)
   self.assertEqual('candidate_changed',result['reason'])
 def test_exhausted_iterations_cannot_be_reset_by_resuming(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);raw={**config(),'max_iterations':1};first=agent_loop.run(root,raw,runtime('claim'),approved=True)
   second=agent_loop.run(root,raw,runtime(),approved=True,run_id=first['run_id'])
   self.assertEqual('iteration_limit',second['reason']);self.assertEqual(1,second['iteration']);self.assertEqual('VALUE = 0\n',(root/'src/value.py').read_text())
 def test_unknown_usage_crash_and_process_timeout_cannot_be_retried_for_free(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);first=agent_loop.run(root,config(),runtime('crash'),approved=True)
   second=agent_loop.run(root,config(),runtime(),approved=True,run_id=first['run_id'])
   self.assertEqual('reconciliation_required',second['reason']);self.assertEqual(1,second['iteration'])
 def test_reviewed_reconciliation_retains_effect_history_and_charges_unknown_queries(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);first=agent_loop.run(root,config(),runtime('pending'),approved=True)
   with self.assertRaises(ValueError):agent_loop.reconcile(root,first['run_id'],approved=False)
   result=agent_loop.reconcile(root,first['run_id'],approved=True)
   self.assertFalse(result['pending']);self.assertTrue(any(e['status']=='reconciled' for e in result['events']));self.assertFalse(result['cost_known'])
   second=agent_loop.run(root,config(),runtime(),approved=True,run_id=first['run_id'])
   self.assertEqual('usage_unavailable',second['reason'])

class MethodologyMatrixTests(unittest.TestCase):
 def test_all_project_types_locales_and_methodologies_keep_their_original_gates(self):
  from aikya.workflows.sdd import engine as sdd
  for kind in ('development','infrastructure','devops'):
   for locale in ('en','es'):
    for method in ('odd','sdd'):
     with self.subTest(kind=kind,locale=locale,method=method),tempfile.TemporaryDirectory() as tmp:
      root=project(tmp,method,kind,locale);raw=config()
      if method=='sdd':
       sdd.initialize(root,{'id':'SPEC-001','title':'Value','objective':'Set one','requirements':[{'id':'REQ-001','description':'Value equals one','acceptance':['Value is one']}],'nonfunctional':[],'questions':[]})
       sdd.approve(root,'SPEC-001','spec','fixture-human');sdd.create_plan(root,'SPEC-001',{'design':'Set the scoped value.','decisions':['Use the fixture file.'],'risks':['Synthetic only.'],'testing':'Check the value.'});sdd.approve(root,'SPEC-001','plan','fixture-human')
       sdd.create_tasks(root,'SPEC-001',{'tasks':[{'id':'TASK-001','description':'Set one','requirements':['REQ-001'],'depends_on':[]}]});sdd.approve(root,'SPEC-001','tasks','fixture-human')
       approvals=sdd.load(root,'SPEC-001')[1]['approvals'];raw.update(command='aikya-implement',work_id='SPEC-001')
      result=agent_loop.run(root,raw,runtime(),approved=True);self.assertEqual('completed',result['status'])
      if method=='sdd':
       state=sdd.load(root,'SPEC-001')[1];self.assertEqual(approvals,state['approvals']);self.assertIsNone(state['verification']);self.assertEqual('done',state['tasks'][0]['status'])
      text=(root/'aikya/docs/loops'/result['run_id']/'summary.md').read_text()
      self.assertIn('# Ejecución' if locale=='es' else '# Agent loop',text);self.assertTrue(text.endswith('GENERATED BY AIKYA HARNESS\n'))

class ConcurrentAndBudgetTests(unittest.TestCase):
 def test_budget_exhaustion_stops_before_review_and_timeout_does_not_reset_on_resume(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);raw={**config(),'max_cost_usd':.0005};result=agent_loop.run(root,raw,runtime(),approved=True)
   self.assertEqual('cost_limit',result['reason']);self.assertEqual(1,len(result['results']))
   again=agent_loop.run(root,raw,runtime(),approved=True,run_id=result['run_id']);self.assertEqual(1,len(again['results']))
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);raw={**config(),'timeout_seconds':1};raw['checks']=[{**check,'timeout_seconds':1} for check in raw['checks']]
   result=agent_loop.run(root,raw,runtime('hang'),approved=True);self.assertEqual('time_limit',result['reason'])
   again=agent_loop.run(root,raw,runtime(),approved=True,run_id=result['run_id']);self.assertEqual('reconciliation_required',again['reason']);self.assertEqual(1,again['iteration'])
 def test_two_callers_cannot_complete_the_same_candidate_concurrently(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);out=[]
   def execute():
    try:out.append(agent_loop.run(root,config(),runtime('slow_write'),approved=True))
    except ValueError as exc:out.append({'error':str(exc)})
   first=threading.Thread(target=execute);first.start()
   limit=time.monotonic()+3
   while not list((root/'aikya/docs/loops').glob('*/state.json')) and time.monotonic()<limit:time.sleep(.02)
   second=threading.Thread(target=execute);second.start();first.join(5);second.join(5)
   self.assertFalse(first.is_alive());self.assertFalse(second.is_alive())
   self.assertEqual(1,sum(v.get('status')=='completed' for v in out));self.assertEqual(1,sum('error' in v for v in out))

class UserInterruptTests(unittest.TestCase):
 def test_user_interrupt_is_recorded_without_exposing_an_uncaught_traceback(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp)
   def interrupted():raise KeyboardInterrupt()
   result=agent_loop.run(root,config(),runtime(),approved=True,cancel=interrupted)
   self.assertEqual('interrupted',result['status']);self.assertEqual('cancelled',result['reason'])

if __name__=='__main__':unittest.main()
