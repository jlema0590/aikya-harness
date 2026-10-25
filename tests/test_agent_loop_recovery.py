"""Uncertain effects and accumulated budgets cannot be cleared by restarting."""
import importlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
from agent_loop_support import project,config,runtime
class RecoveryTests(unittest.TestCase):
 def module(self):
  self.assertIsNotNone(importlib.util.find_spec('aikya.core.loop'),'Missing durable loop');return importlib.import_module('aikya.core.loop')
 def test_unfinished_effect_is_not_replayed_on_resume(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);first=m.run(root,config(),runtime('pending'),approved=True)
   second=m.run(root,config(),runtime(),approved=True,run_id=first['run_id'])
   self.assertEqual('reconciliation_required',second['reason']);self.assertEqual('VALUE = 0\n',(root/'src/value.py').read_text())
 def test_recovery_rejects_a_different_checkout_and_modified_scope(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);first=m.run(root,{**config(),'max_iterations':1},runtime('claim'),approved=True)
   moved=Path(tmp)/'moved';shutil.copytree(root,moved)
   with self.assertRaises(ValueError):m.run(moved,{**config(),'max_iterations':1},runtime(),approved=True,run_id=first['run_id'])
   with self.assertRaises(ValueError):m.run(root,config(),runtime(),approved=True,run_id=first['run_id'])
 def test_session_cumulative_totals_and_duplicate_results_do_not_double_charge(self):
  self.assertIsNotNone(importlib.util.find_spec('aikya.core.checkpoints'),'Missing durable accounting');m=importlib.import_module('aikya.core.checkpoints')
  state={'cost_usd':0.0,'sessions':{},'results':{},'cost_known':True}
  one={'id':'a','session_id':'s','cost_usd':0.01};m.account(state,one);m.account(state,one)
  m.account(state,{'id':'b','session_id':'s','cost_usd':0.015});m.account(state,{'id':'c','session_id':'other','cost_usd':0.005})
  self.assertAlmostEqual(0.02,state['cost_usd'])
  with self.assertRaises(ValueError):m.account(state,{'id':'a','session_id':'s','cost_usd':0.5})

class CompletionRecoveryTests(unittest.TestCase):
 def test_completed_resume_is_idempotent_but_changed_evidence_is_rejected(self):
  from aikya.core import loop as agent_loop
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);first=agent_loop.run(root,config(),runtime(),approved=True)
   second=agent_loop.run(root,config(),runtime('crash'),approved=True,run_id=first['run_id'])
   self.assertEqual('completed',second['status']);self.assertEqual(first['iteration'],second['iteration'])
   (root/'aikya/docs/loops'/first['run_id']/'evidence.json').write_text('{}')
   with self.assertRaises(ValueError):agent_loop.run(root,config(),runtime(),approved=True,run_id=first['run_id'])

class UsageAccountingTests(unittest.TestCase):
 def test_reported_session_tokens_are_counted_once_and_missing_usage_stays_unknown(self):
  from aikya.core import checkpoints as store
  data={'cost_usd':0.0,'cost_known':True,'sessions':{},'results':{}}
  def result(ident,session,cost,ins,outs):return {'id':ident,'session_id':session,'cost_usd':cost,'model_usage':{'fixture':{'inputTokens':ins,'outputTokens':outs,'cacheReadInputTokens':0,'cacheCreationInputTokens':0}}}
  first=result('a','one',.01,5,7);store.account(data,first);store.account(data,first);store.account(data,result('b','one',.02,6,9));store.account(data,result('c','two',.005,2,3))
  self.assertEqual(8,data['token_totals']['inputTokens']);self.assertEqual(12,data['token_totals']['outputTokens']);self.assertTrue(data['tokens_known'])
  store.account(data,{'id':'d','session_id':'three','cost_usd':.001});self.assertFalse(data['tokens_known'])

class UsageAtomicityTests(unittest.TestCase):
 def test_malformed_usage_cannot_partially_mutate_the_durable_budget(self):
  import copy; from aikya.core import checkpoints as store
  data={'cost_usd':0.0,'cost_known':True,'sessions':{},'results':{}};before=copy.deepcopy(data)
  with self.assertRaises(ValueError):store.account(data,{'id':'a','session_id':'s','cost_usd':float('nan'),'model_usage':{'fixture':{'inputTokens':5,'outputTokens':7,'cacheReadInputTokens':0,'cacheCreationInputTokens':0}}})
  self.assertEqual(before,data)

class CheckpointCrashTests(unittest.TestCase):
 def test_interrupted_summary_projection_remains_recoverable_without_overwriting_custom_reports(self):
  from unittest.mock import patch
  from aikya.core import loop as agent_loop; from aikya.core import checkpoints as store
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);first=agent_loop.run(root,config(),runtime(),approved=True,cancel=lambda:True);data=store.load(root,first['run_id']);data['reason']='checkpoint_probe'
   original=store.atomic
   def fail_summary(path,value):
    if path.name=='summary.md':raise OSError('Synthetic cut after the authoritative state checkpoint')
    return original(path,value)
   with patch.object(store,'atomic',side_effect=fail_summary):
    with self.assertRaises(OSError):store.save(root,data)
   recovered=store.load(root,first['run_id']);self.assertEqual('checkpoint_probe',recovered['reason'])
   store.save(root,recovered);self.assertEqual('checkpoint_probe',store.load(root,first['run_id'])['reason'])
   (root/'aikya/docs/loops'/first['run_id']/'summary.md').write_text('Custom team summary\n')
   with self.assertRaises(ValueError):agent_loop.reconcile(root,first['run_id'],approved=True)
 def test_source_change_in_the_completion_checkpoint_never_closes_the_task(self):
  from unittest.mock import patch
  from aikya.core import loop as agent_loop; from aikya.core import checkpoints as store; from aikya.workflows import odd as odd_engine
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);original=store.save;changed=False
   def change_after_intent(root_path,data):
    nonlocal changed
    value=original(root_path,data)
    if 'completion' in data['pending'] and not changed:
     changed=True;(root/'src/value.py').write_text('VALUE = 2\n')
    return value
   with patch.object(store,'save',side_effect=change_after_intent):result=agent_loop.run(root,config(),runtime(),approved=True)
   self.assertEqual('candidate_changed',result['reason']);self.assertNotEqual('completed',result['status']);self.assertEqual('todo',odd_engine.load(root,'value')['tasks'][0]['status'])

if __name__=='__main__':unittest.main()
