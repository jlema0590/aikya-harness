"""Installed onboarding, hook correlation and preservation of user configuration."""
import runtime_support
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aikya.core import state as state
from aikya.installation.registration import setup
class ExecutionIntegrationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.cache=self.base/'cache';self.root=self.base/'project';self.env={**os.environ,'AIKYA_EXECUTION_CACHE':str(self.cache),'PYTHONDONTWRITEBYTECODE':'1'}
 def cli(self,*args):return subprocess.run([sys.executable,'-B',str(ROOT / 'src/aikya/cli/main.py'),*args,'--target',str(self.root),'--session','fixture'],text=True,capture_output=True,env=self.env)
 def context(self):return {'root':str(self.root),'session_id':'fixture','cache_root':str(self.cache)}
 def test_initial_choice_waits_then_preview_completes_without_project_writes(self):
  self.root.mkdir();(self.root/'pom.xml').write_text('<project/>');before=list(self.root.iterdir())
  proc=self.cli('analyze','--dry-run');self.assertEqual(4,proc.returncode,proc.stderr);self.assertEqual('waiting',state.read_active(self.context())['phases']['plan']['status'])
  proc=self.cli('analyze','--methodology','odd','--dry-run');self.assertEqual(0,proc.returncode,proc.stderr)
  run=state.read_active(self.context());self.assertEqual('completed',run['status']);self.assertEqual('skipped',run['phases']['implement']['status']);self.assertEqual(before,list(self.root.iterdir()))
 def test_registered_scope_contains_runtime_and_preserves_custom_bar(self):
  self.root.mkdir();config=self.root/'.claude/settings.json';config.parent.mkdir();config.write_text(json.dumps({'statusLine':{'type':'command','command':'custom-status'}}))
  setup(ROOT,self.root,'project',home=self.base/'home')
  current=json.loads(config.read_text());self.assertEqual('custom-status',current['statusLine']['command']);self.assertIn('UserPromptSubmit',current['hooks'])
  runtime=self.root/'.aikya/runtime'
  for name in ('odd_engine.py','execution_state.py','execution_observer.py','aikya_statusline.py'):self.assertTrue((runtime/name).is_file(),name)
  self.assertTrue((self.root/'.aikya/visibility-proposed.json').is_file())
  event={'hook_event_name':'UserPromptSubmit','prompt':'/aikya-init','cwd':str(self.root),'session_id':'fixture'}
  proc=subprocess.run([sys.executable,'-B',str(runtime/'execution_observer.py'),'hook'],input=json.dumps(event),capture_output=True,text=True,env=self.env)
  self.assertEqual(0,proc.returncode,proc.stderr);self.assertEqual('aikya-init',state.read_active(self.context())['command']);self.assertEqual('',proc.stdout)
 def test_hook_and_cli_share_one_invocation_and_nested_skills_keep_parent(self):
  from aikya.middleware.observer import observe
  self.root.mkdir();(self.root/'pom.xml').write_text('<project/>')
  run=observe(self.context(),{'hook_event_name':'UserPromptSubmit','prompt':'/aikya-analyze --dry-run'})
  nested=observe(self.context(),{'hook_event_name':'PreToolUse','tool_name':'Skill','tool_input':{'skill':'aikya-docs'}})
  self.assertEqual(run['run_id'],nested['run_id'])
  proc=self.cli('analyze','--methodology','odd','--dry-run');self.assertEqual(0,proc.returncode,proc.stderr)
  self.assertEqual(run['run_id'],state.read_active(self.context())['run_id'])
 def test_quality_runner_records_process_failure_without_marking_validate_done(self):
  import importlib.util
  from unittest.mock import patch
  self.root.mkdir();run=state.start_run(self.context(),'aikya-quality');context={**self.context(),'run_id':run['run_id']}
  config=self.root/'harness.json';config.write_text(json.dumps({'checks':[{'name':'synthetic-process','required':True,'command':[sys.executable,'-c','raise SystemExit(1)'],'cwd':'.'}]}))
  spec=runtime_support.module_spec('fixture_runner',ROOT/'src/aikya/resources/project_template/scripts/harness/run_checks.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner);runner=getattr(runner,'_module',runner);runner.ROOT=self.root
  with patch.dict(os.environ,{**self.env,'CLAUDE_SESSION_ID':'fixture'}):self.assertEqual(1,runner.run(config))
  value=state.read_snapshot(context);self.assertEqual('failed',value['phases']['validate']['status']);self.assertNotEqual('completed',value['status'])
 def test_quality_completion_after_rework_cannot_certify_the_new_candidate(self):
  from unittest.mock import patch
  from aikya.middleware.events import CheckEvents
  self.root.mkdir();run=state.start_run(self.context(),'aikya-quality');context={**self.context(),'run_id':run['run_id']}
  with patch.dict(os.environ,{**self.env,'CLAUDE_SESSION_ID':'fixture'}):
   observer=CheckEvents(self.root);state.record_event(context,{'phase':'implement','status':'running','actor_id':'developer'})
   observer.process('Original candidate only',0);observer.finish(0)
  self.assertEqual('pending',state.read_snapshot(context)['phases']['validate']['status'])
 def test_unmet_strict_requirements_are_blocked_before_initialization(self):
  from unittest.mock import patch
  from aikya.cli import main as aikya_cli; import contextlib; import io
  answers=self.base/'answers.json';answers.write_bytes((ROOT/'examples/next-react/answers.json').read_bytes())
  with patch.dict(os.environ,self.env),patch.object(aikya_cli,'check',return_value={'ready':False}),contextlib.redirect_stdout(io.StringIO()):
   code=aikya_cli.main(['init','--target',str(self.root),'--answers',str(answers),'--methodology','odd','--strict','--session','fixture'])
  self.assertEqual(4,code);self.assertFalse(self.root.exists());self.assertEqual('blocked',state.read_active(self.context())['status'])
 def test_public_skills_preserve_the_complete_footer_instruction_and_methodology_guard(self):
  for path in (ROOT/'src/aikya/resources/commands').glob('*/SKILL.md'):
   body=path.read_text()
   if 'the exact line `' in body:self.assertIn('the exact line `GENERATED BY AIKYA HARNESS`.',body,str(path))
  self.assertIn('## Methodology preservation',(ROOT/'src/aikya/resources/commands/aikya-answers/SKILL.md').read_text())
 def test_custom_coupled_runtime_blocks_upgrade_before_any_project_mutation(self):
  from aikya.discovery.analyze import execute
  self.root.mkdir();(self.root/'pom.xml').write_text('<project/>');self.assertEqual('READY',execute(self.root,approved=True,methodology='odd')['status'])
  runtime=self.root/'aikya/scripts/harness/execution_state.py';runtime.write_text(runtime.read_text()+'\n# Local customization retained.\n')
  before={p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
  result=execute(self.root,approved=True,refresh=True)
  self.assertEqual('NEEDS_REVIEW',result['status']);self.assertFalse(result['writes'])
  self.assertEqual(before,{p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
 def test_approved_adoption_records_only_real_local_checks(self):
  self.root.mkdir();(self.root/'pom.xml').write_text('<project/>')
  proc=self.cli('analyze','--methodology','odd','--approved');self.assertEqual(0,proc.returncode,proc.stderr)
  run=state.read_active(self.context());self.assertEqual('completed',run['status']);self.assertEqual('completed',run['phases']['security']['status']);self.assertEqual('skipped',run['phases']['review']['status'])
  self.assertTrue(all(v.get('observed_model') is None for phase in run['phases'].values() for v in phase['actors'].values()))
  proc=subprocess.run([sys.executable,'-B',str(self.root/'aikya/scripts/harness/odd_engine.py'),'classify','--input',str(self.base/'facts.json')],capture_output=True,text=True,env=self.env)
  self.assertNotIn('ModuleNotFoundError',proc.stderr)
if __name__=='__main__':unittest.main()
