"""Local display must preserve uncertainty and never alter project files."""
import importlib,json,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
class ExecutionUITests(unittest.TestCase):
 def test_compact_details_missing_metrics_and_narrow_untrusted_labels(self):
  ui=importlib.import_module('aikya.middleware.statusline')
  snapshot={'command':'aikya-init','methodology':'odd','phase':'implement','status':'running','activity':'Creating approved files','phases':{'implement':{'status':'running','actors':{'main':{'observed_model':None}}},'security':{'status':'pending','reason':'','actors':{}}}}
  result=ui.render_status(snapshot,{},width=160)
  self.assertIn('Implement',result);self.assertIn('Running',result);self.assertIn('N/D',result);self.assertNotIn('0%',result);self.assertNotIn('Security',result)
  self.assertIn('Security: Pending',ui.render_status(snapshot,{},width=160,detail=True))
  narrow=ui.render_status(snapshot,{'model':'observed-model'},width=42)
  self.assertIn('Implement',narrow);self.assertIn('Running',narrow);self.assertIn('aikya-init',narrow)
  snapshot['activity']='bad\x1b[31m\n'+'x'*200
  for line in ui.render_status(snapshot,{'model':'actual-model'},width=42).splitlines():self.assertLessEqual(len(line),42);self.assertNotIn('\x1b',line)
 def test_resolved_subagent_model_is_never_inherited(self):
  ui=importlib.import_module('aikya.middleware.subagent_statusline')
  rows=ui.render_actor_rows({'model':{'id':'main-model'},'tasks':[{'id':'1','agentType':'reviewer','status':'running','model':'resolved-review-model','tokenCount':123},{'id':'2','agentType':'planner','status':'running'}]}, {})
  self.assertEqual('resolved-review-model',rows[0]['model']);self.assertIsNone(rows[1]['model']);self.assertIsNone(rows[1]['tokens'])
 def test_statusline_stdin_and_empty_metrics_cache_do_not_write_project(self):
  from aikya.middleware import metrics as metrics
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);root=base/'project';root.mkdir();cache=base/'cache';context={'root':str(root),'session_id':'s','cache_root':str(cache)}
   metrics.cache_metrics(context,{},now=time.time())
   self.assertIsNone(metrics.read_metrics(context)['account_seven_day_pct'])
   env={**os.environ,'AIKYA_EXECUTION_CACHE':str(cache),'PYTHONDONTWRITEBYTECODE':'1'}
   process=subprocess.run([sys.executable,'-B',str(ROOT / 'src/aikya/middleware/statusline.py')],input=json.dumps({'cwd':str(root),'session_id':'s','model':{'id':'observed-example'},'context_window':{'used_percentage':0}}),text=True,capture_output=True,env=env)
   self.assertEqual(0,process.returncode,process.stderr);self.assertIn('observed-example',process.stdout);self.assertIn('Context: 0%',process.stdout);self.assertEqual([],list(root.iterdir()))
 def test_subagent_cli_emits_official_json_rows(self):
  payload={'columns':70,'tasks':[{'id':'1','agentType':'reviewer','status':'running','model':'actual','tokenCount':123}]}
  proc=subprocess.run([sys.executable,'-B',str(ROOT / 'src/aikya/middleware/subagent_statusline.py')],input=json.dumps(payload),capture_output=True,text=True)
  row=json.loads(proc.stdout);self.assertEqual('1',row['id']);self.assertIn('actual',row['content']);self.assertLessEqual(len(row['content']),70)
 def test_compact_uses_the_active_actor_model_and_never_assigns_main_to_python(self):
  from aikya.middleware.statusline import render_status
  value={'command':'aikya-quality','phase':'review','status':'running','phases':{'review':{'status':'running','actors':{'reviewer-7':{'status':'running','observed_model':'review-model'}}}}}
  output=render_status(value,{'model':'main-model'},200);self.assertIn('review-model',output.splitlines()[0]);self.assertNotIn('main-model',output.splitlines()[0])
  value['phases']['review']['actors']={'main':{'status':'running','observed_model':'previous-model'}}
  self.assertIn('current-runtime-model',render_status(value,{'model':'current-runtime-model'},200).splitlines()[0])
  value['phase']='validate';value['phases']={'validate':{'status':'running','actors':{'main':{'status':'completed','observed_model':'main-model'},'local-python':{'status':'running','observed_model':None}}}}
  output=render_status(value,{'model':'main-model'},200);self.assertIn('Python (local)',output);self.assertNotIn('main-model',output.splitlines()[0])
  value['phase']='review';value['phases']={'review':{'status':'running','actors':{'unknown-reviewer':{'status':'running','observed_model':None}}}}
  self.assertIn('N/D',render_status(value,{'model':'main-model'},200).splitlines()[0])
 def test_settings_preserve_custom_status_and_do_not_chain_shell_commands(self):
  from aikya.middleware.configuration import merge_visibility
  custom={'statusLine':{'type':'command','command':'my-custom-status'},'hooks':{'UserPromptSubmit':[{'hooks':[{'type':'command','command':'custom-hook'}]}]}}
  before=json.loads(json.dumps(custom));merged,proposals=merge_visibility(custom,'python3 "/runtime/execution_observer.py" hook','python3 "/runtime/aikya_statusline.py"')
  self.assertEqual(before,custom);self.assertEqual(before['statusLine'],merged['statusLine']);self.assertIn('statusLine',proposals)
  self.assertEqual(2,len(merged['hooks']['UserPromptSubmit']));again,proposal=merge_visibility(merged,'python3 "/runtime/execution_observer.py" hook','python3 "/runtime/aikya_statusline.py"');self.assertEqual(merged,again)
  self.assertNotIn('&&',json.dumps(merged));self.assertNotIn(';',json.dumps(merged))
if __name__=='__main__':unittest.main()
