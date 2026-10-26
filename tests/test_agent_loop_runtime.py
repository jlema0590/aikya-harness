"""Exercise real worker protocol, termination and SDK permission boundaries."""
import importlib,importlib.util,sys,tempfile,time,unittest
from pathlib import Path
from agent_loop_support import project,runtime
class RuntimeTests(unittest.TestCase):
 def module(self):
  self.assertIsNotNone(importlib.util.find_spec('aikya.core.runtime'),'Missing optional runtime adapter');return importlib.import_module('aikya.core.runtime')
 def test_tools_are_denied_outside_the_reviewed_file_set_and_during_review(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);request={'root':str(root),'files':['src/value.py'],'context_files':[],'phase':'implement'}
   for tool,path in (('Write','../outside'),('Read','.env'),('Bash','src/value.py'),('Skill','src/value.py'),('Write','.claude/settings.json')):
    self.assertFalse(m.tool_allowed(request,tool,{'file_path':path}))
   self.assertTrue(m.tool_allowed(request,'Write',{'file_path':str(root/'src/value.py')}))
   self.assertFalse(m.tool_allowed({**request,'phase':'review'},'Write',{'file_path':'src/value.py'}))
   (root/'src/link.py').symlink_to(root/'src/value.py')
   self.assertFalse(m.tool_allowed({**request,'files':['src/link.py']},'Write',{'file_path':'src/link.py'}))
 def test_hung_or_cancelled_process_is_terminated_and_malformed_data_rejected(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);request={'root':str(root),'files':['src/value.py'],'phase':'implement','timeout_seconds':0.15}
   for mode,cancel,exception in (('hang',lambda:False,TimeoutError),('hang',lambda:True,InterruptedError),('malformed',lambda:False,ValueError)):
    started=time.monotonic()
    with self.assertRaises(exception):runtime(mode).execute(request,lambda e:None,cancel)
    self.assertLess(time.monotonic()-started,3)
 def test_optional_sdk_is_not_imported_for_policy_checks(self):
  self.module();self.assertNotIn('claude_agent_sdk',sys.modules)

class RuntimeAttackTests(unittest.TestCase):
 def test_timeout_kills_a_spawned_descendant_and_flooded_protocol_is_bounded(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=project(tmp);request={'root':str(root),'files':['src/value.py'],'phase':'implement','timeout_seconds':.2}
   with self.assertRaises(TimeoutError):runtime('grandchild').execute(request,lambda e:None)
   time.sleep(.9);self.assertFalse((root/'child-survived').exists())
   with self.assertRaises(ValueError):runtime('flood').execute({**request,'timeout_seconds':2},lambda e:None)

if __name__=='__main__':unittest.main()
