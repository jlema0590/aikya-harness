import runtime_support
"""Installed command routing stays opt-in and portable across registration scopes."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from agent_loop_support import ROOT,project,config,runtime
class LoopInstallationTests(unittest.TestCase):
 def test_managed_packaging_mirrors_are_backed_up_and_retired_but_custom_ones_stay(self):
  from aikya.installation import registration as aikya_setup; import hashlib
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'project';home=Path(tmp)/'home';folder=root/'.aikya/runtime';previous={}
   for name in ('external_skills.py','skills_registry.py'):
    mirror=folder/'template/scripts/harness'/name;mirror.parent.mkdir(parents=True,exist_ok=True)
    raw=(ROOT/name).read_bytes();mirror.write_bytes(raw);previous[mirror.relative_to(folder).as_posix()]=hashlib.sha256(raw).hexdigest()
   custom=folder/'template/scripts/harness/skills_registry.py';custom.write_bytes(custom.read_bytes()+b'\n# Owner customization.\n')
   (folder/'manifest.json').write_text(json.dumps({'files':previous}))
   aikya_setup.setup(ROOT,root,'project',home=home)
   self.assertFalse((folder/'template/scripts/harness/external_skills.py').exists())
   self.assertEqual(runtime_support.generated_bytes('external_skills.py'),(folder/'retired-assets/template/scripts/harness/external_skills.py').read_bytes())
   self.assertIn(b'Owner customization',custom.read_bytes())
   aikya_setup.setup(ROOT,root,'project',home=home)
   self.assertIn(b'Owner customization',custom.read_bytes())

 def test_init_never_accepts_the_loop_switch_or_writes_a_dossier(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'new'
   p=subprocess.run([sys.executable,str(ROOT / 'src/aikya/cli/main.py'),'init','--target',str(root),'--agent-loop'],capture_output=True,text=True)
   self.assertEqual(2,p.returncode);self.assertFalse(root.exists())
 def test_loop_modules_ship_in_global_project_and_initialized_runtime_without_sdk_dependency(self):
  from aikya.installation import registration as aikya_setup; from aikya.installation import facade as install
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp)
   for scope in ('global','project'):
    root=base/scope;home=base/(scope+'home');aikya_setup.setup(ROOT,root,scope,home=home)
    folder=home/'.claude/aikya-harnes' if scope=='global' else root/'.aikya/runtime'
    for name in ('agent_loop.py','agent_runtime.py','agent_loop_state.py','agent_memory.py','memory_store.py','agent_memory_extract.py','durable_io.py','code_quality.py','requirements-agent-loop.txt','docs/AGENT_LOOP.md'):self.assertTrue((folder/name).is_file(),name)
   root=base/'installed';profile=install.validated(json.loads((ROOT/'examples/next-react/answers.json').read_text()),root);install.install(root,profile,{'modules':[],'findings':[]},docs_lang='en')
   for name in ('agent_loop.py','agent_runtime.py','agent_loop_state.py','agent_memory.py','memory_store.py','agent_memory_extract.py','durable_io.py','code_quality.py','requirements-agent-loop.txt','docs/AGENT_LOOP.md'):self.assertTrue((root/'aikya/scripts/harness'/name).is_file())
 def test_cli_routes_feature_loop_only_when_explicit_and_reports_optional_sdk_unavailable(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);settings=root/'loop.json';settings.write_text(json.dumps(config()))
   p=subprocess.run([sys.executable,str(ROOT / 'src/aikya/cli/main.py'),'feature','--target',str(root),'--agent-loop','--loop-input',str(settings),'--approved'],capture_output=True,text=True)
   self.assertEqual(4,p.returncode,p.stderr);self.assertEqual('optional_sdk_missing',json.loads(p.stdout)['reason']);self.assertFalse((root/'aikya/docs/loops').exists())

if __name__=='__main__':unittest.main()
