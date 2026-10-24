"""Execution snapshots must remain truthful across concurrency and interruption."""
import concurrent.futures,importlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
class ExecutionStateTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
  self.context={'root':str(self.base/'project'),'session_id':'s1','cache_root':str(self.base/'cache')}
 def module(self):
  self.assertIsNotNone(importlib.util.find_spec('execution_state'),'Missing execution state manager');return importlib.import_module('execution_state')
 def start(self,command='aikya-init'):
  m=self.module();run=m.start_run(self.context,command);return m,{**self.context,'run_id':run['run_id']}
 def test_read_only_start_uses_private_cache_and_phase_completion_needs_evidence(self):
  m,c=self.start();self.assertFalse(Path(c['root']).exists())
  m.record_event(c,{'id':'e1','phase':'explore','status':'running','activity':'Inspecting project'})
  with self.assertRaises(ValueError):m.record_event(c,{'id':'e2','phase':'validate','status':'completed'})
  with self.assertRaises(ValueError):m.record_event(c,{'id':'e3','phase':'security','status':'skipped'})
  m.record_event(c,{'id':'e4','phase':'explore','status':'completed','evidence':[{'kind':'observation','result':'recorded','check':'Workspace inspected'}]})
  state=m.read_snapshot(c);self.assertEqual('completed',state['phases']['explore']['status']);self.assertEqual('running',state['status'])
 def test_failure_blocks_success_and_rework_invalidates_later_results(self):
  m,c=self.start();m.record_event(c,{'id':'v1','phase':'validate','status':'failed','reason':'Syntax failed'})
  with self.assertRaises(ValueError):m.finish_run(c,'completed')
  m.record_event(c,{'id':'i1','phase':'implement','status':'running','activity':'Correcting approved file'})
  self.assertEqual('pending',m.read_snapshot(c)['phases']['validate']['status'])
  self.assertTrue(any(e.get('status')=='failed' for e in m.read_snapshot(c)['history']))
  m.finish_run(c,'interrupted');self.assertEqual('interrupted',m.read_snapshot(c)['status'])
 def test_sessions_worktrees_duplicate_events_and_concurrent_updates_are_isolated(self):
  m,c=self.start();other={**c,'root':str(self.base/'other')};other_run=m.start_run(other,'aikya-feature');other['run_id']=other_run['run_id']
  def emit(i):return m.record_event(c,{'id':'event-'+str(i),'phase':'explore','status':'running','activity':'Inspecting fixture'})
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(emit,range(12)))
  emit(1);self.assertEqual(12,len([e for e in m.read_snapshot(c)['history'] if e['id'].startswith('event-')]))
  self.assertEqual('pending',m.read_snapshot(other)['phases']['explore']['status'])
  self.assertIsNone(m.read_active({**c,'session_id':'other-session'}))
 def test_all_registered_commands_have_recipes_and_unrelated_text_starts_nothing(self):
  self.module();recipes=importlib.import_module('command_workflows');observer=importlib.import_module('execution_observer')
  from aikya.installation.registration import BOOTSTRAP_COMMANDS
  for command in BOOTSTRAP_COMMANDS:self.assertEqual(command,recipes.recipe(command,'odd')['command'])
  self.assertIsNone(observer.observe(self.context,{'hook_event_name':'UserPromptSubmit','prompt':'Explain /aikya-init before I run it.'}))
  self.assertFalse((self.base/'project').exists())
  run=observer.observe(self.context,{'hook_event_name':'UserPromptSubmit','prompt':'/aikya-init','prompt_id':'p1'})
  duplicate=observer.observe(self.context,{'hook_event_name':'PreToolUse','tool_name':'Skill','tool_input':{'skill':'aikya-init'}})
  self.assertEqual(run['run_id'],duplicate['run_id'])
 def test_review_and_security_success_rejects_failed_or_missing_checks(self):
  m,c=self.start()
  for phase in ('validate','security','review'):
   with self.assertRaises(ValueError):m.record_event(c,{'phase':phase,'status':'completed','evidence':[{'kind':'process','check':'fixture','exit_code':1}]})
  m.record_event(c,{'candidate_generation':m.read_snapshot(c).get('candidate_generation',0),'phase':'security','status':'completed','evidence':[{'kind':'process','check':'fixture-only security check','exit_code':0}]})
  self.assertEqual('completed',m.read_snapshot(c)['phases']['security']['status'])
 def test_superseded_runs_and_parallel_actors_cannot_report_stale_success(self):
  m,c=self.start();new=m.start_run(self.context,'aikya-feature')
  with self.assertRaises(ValueError):m.record_event(c,{'phase':'explore','status':'running'})
  c={**self.context,'run_id':new['run_id']}
  m.record_event(c,{'phase':'validate','status':'running','actor_id':'worker'})
  evidence=[{'kind':'process','check':'actual fixture check','exit_code':0}]
  value=m.record_event(c,{'candidate_generation':m.read_snapshot(c).get('candidate_generation',0),'phase':'validate','status':'completed','evidence':evidence})
  self.assertEqual('running',value['phases']['validate']['status'])
  value=m.record_event(c,{'phase':'validate','status':'completed','actor_id':'worker','evidence':evidence})
  self.assertEqual('completed',value['phases']['validate']['status'])
  with self.assertRaises(ValueError):m.record_event(c,{'phase':'explore','status':'running','evidence':None})
 def test_all_public_command_protocols_close_with_scoped_fixture_evidence(self):
  import hashlib
  from aikya.installation.registration import BOOTSTRAP_COMMANDS
  from aikya.middleware.observer import observe
  from aikya.middleware.commands import recipe
  for command in BOOTSTRAP_COMMANDS:
   context={**self.context,'session_id':command};value=observe(context,{'hook_event_name':'UserPromptSubmit','prompt':'/'+command});context['run_id']=value['run_id'];m=self.module()
   for phase in recipe(command)['required']:
    m.record_event(context,{'phase':phase,'status':'running'})
    evidence={'kind':'inspection' if phase in ('validate','security') else 'observation','check':'Synthetic protocol fixture only','result':'passed' if phase in ('validate','security') else 'recorded'}
    if phase=='review':evidence={'kind':'review','result':'passed','check':'Protocol recipe inspected','reviewer':'fixture-inspector','candidate':hashlib.sha256(json.dumps(recipe(command),sort_keys=True).encode()).hexdigest()}
    m.record_event(context,{'phase':phase,'status':'completed','evidence':[evidence]})
   self.assertEqual('completed',m.finish_run(context,'completed')['status'],command)
 def test_closed_or_superseded_runs_cannot_be_reclosed_as_success(self):
  m,c=self.start()
  for phase in ('explore','plan','implement','validate','security'):
   m.record_event(c,{'candidate_generation':m.read_snapshot(c).get('candidate_generation',0),'phase':phase,'status':'completed','evidence':[{'kind':'inspection' if phase in ('validate','security') else 'observation','result':'passed' if phase in ('validate','security') else 'recorded','check':'Scoped fixture only'}]})
  m.finish_run(c,'interrupted')
  with self.assertRaises(ValueError):m.finish_run(c,'completed')
  self.assertEqual('interrupted',m.read_snapshot(c)['status'])
 def test_prompt_identity_deduplicates_hooks_but_separates_repeated_commands_and_late_failures(self):
  from aikya.middleware.observer import observe
  first=observe(self.context,{'hook_event_name':'UserPromptSubmit','prompt':'/aikya-init','prompt_id':'first'})
  duplicate=observe(self.context,{'hook_event_name':'UserPromptSubmit','prompt':'/aikya-init','prompt_id':'first'})
  self.assertEqual(first['run_id'],duplicate['run_id'])
  second=observe(self.context,{'hook_event_name':'UserPromptSubmit','prompt':'/aikya-init','prompt_id':'second'})
  self.assertNotEqual(first['run_id'],second['run_id'])
  c={**self.context,'run_id':second['run_id']};m=self.module();m.record_event(c,{'phase':'implement','status':'running'})
  observe(self.context,{'hook_event_name':'PostToolUseFailure','prompt_id':'first'})
  self.assertEqual('running',m.read_snapshot(c)['phases']['implement']['status'])
 def test_old_check_completion_cannot_validate_a_changed_candidate(self):
  m,c=self.start();m.record_event(c,{'phase':'validate','status':'running','actor_id':'old-check'})
  generation=m.read_snapshot(c).get('candidate_generation',0)
  m.record_event(c,{'phase':'implement','status':'running'})
  with self.assertRaises(ValueError):m.record_event(c,{'phase':'validate','status':'completed','actor_id':'old-check','candidate_generation':generation,'evidence':[{'kind':'process','check':'Old candidate only','exit_code':0}]})
  self.assertEqual('pending',m.read_snapshot(c)['phases']['validate']['status'])
 def test_corrupted_cache_shape_is_rejected_without_overwriting_it(self):
  m,c=self.start();path=m.run_path(c);value=json.loads(path.read_text());value['phases']={};path.write_text(json.dumps(value));before=path.read_bytes()
  with self.assertRaises(ValueError):m.record_event(c,{'phase':'explore','status':'running'})
  self.assertEqual(before,path.read_bytes())
if __name__=='__main__':unittest.main()
