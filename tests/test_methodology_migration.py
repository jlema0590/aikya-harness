"""Onboarding must preserve choices and legacy profiles without silent adoption."""
import importlib,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aikya.installation import facade as install
from aikya.discovery.analyze import execute

class MethodologyMigrationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def helper(self):
  self.assertIsNotNone(importlib.util.find_spec('methodology'),'Missing canonical methodology resolver')
  return importlib.import_module('methodology')
 def test_legacy_and_missing_profiles_normalize_without_mutating_input(self):
  m=self.helper()
  for value,expected in [(None,'odd'),('standard','odd'),('odd','odd'),('sdd','sdd')]:self.assertEqual(expected,m.normalize_methodology(value))
  for value in ('',False,{},'unknown'):
   with self.assertRaises(ValueError):m.normalize_methodology(value)
  for example in ('next-react','infra-terraform-only','devops-kustomize'):
   raw=json.loads((ROOT/'examples'/example/'answers.json').read_text());before=dict(raw)
   self.assertEqual('odd',install.validated({**raw,'methodology':'standard'},self.root)['methodology']);self.assertEqual(before,raw)
 def test_analyze_requires_initial_choice_without_creating_files(self):
  (self.root/'pom.xml').write_text('<project/>');before={p.name:p.read_bytes() for p in self.root.iterdir()}
  result=execute(self.root,approved=True,docs_lang='en')
  self.assertEqual('NEEDS_METHODOLOGY',result['status']);self.assertFalse(result['writes'])
  self.assertEqual(['odd','sdd'],result['methodology_options'])
  self.assertEqual(before,{p.name:p.read_bytes() for p in self.root.iterdir()})
 def test_explicit_choice_survives_preview_install_and_refresh(self):
  self.helper();(self.root/'pom.xml').write_text('<project/>')
  for method in ('odd','sdd'):
   preview=execute(self.root,dry_run=True,methodology=method,docs_lang='en')
   self.assertFalse(preview['writes']);self.assertEqual(method,preview['methodology'])
   result=execute(self.root,approved=True,methodology=method,docs_lang='en');self.assertEqual('READY',result['status'])
   self.assertEqual(method,json.loads((self.root/'.harness/project-profile.json').read_text())['decisions']['methodology'])
   execute(self.root,approved=True,refresh=True,docs_lang='en')
   self.assertEqual(method,json.loads((self.root/'.harness/project-profile.json').read_text())['decisions']['methodology'])
  with self.assertRaises(ValueError):execute(self.root,approved=True,methodology='odd',docs_lang='en')
 def test_init_requires_choice_or_confirmed_answers_and_supports_explicit_flag(self):
  self.helper();raw=json.loads((ROOT/'examples/next-react/answers.json').read_text());raw.pop('methodology',None)
  file=self.root/'answers.json';file.write_text(json.dumps(raw));target=self.root/'new'
  proc=subprocess.run([sys.executable,'-B',str(ROOT / 'src/aikya/cli/main.py'),'init','--target',str(target),'--answers',str(file),'--dry-run'],capture_output=True,text=True)
  self.assertEqual(4,proc.returncode,proc.stderr);self.assertIn('NEEDS_METHODOLOGY',proc.stdout);self.assertFalse(target.exists())
  proc=subprocess.run([sys.executable,'-B',str(ROOT / 'src/aikya/cli/main.py'),'init','--target',str(target),'--answers',str(file),'--methodology','odd','--dry-run','--external','skip'],capture_output=True,text=True)
  self.assertEqual(0,proc.returncode,proc.stderr);self.assertFalse(target.exists());self.assertEqual(raw,json.loads(file.read_text()))

if __name__=='__main__':unittest.main()

class MethodologyBackupTests(unittest.TestCase):
 def test_unsafe_legacy_backup_is_rejected_before_any_project_change(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'project';root.mkdir();outside=Path(tmp)/'outside';outside.mkdir()
   raw=json.loads((ROOT/'examples/next-react/answers.json').read_text());profile=install.validated(raw,root);profile['methodology']='standard';profile['mode']='existing'
   owned=root/'.harness/project-profile.json';owned.parent.mkdir();owned.write_text(json.dumps({'_generated_by':'claude-dev-harness-interactive','decisions':profile}))
   (root/'.harness/backup-odd').symlink_to(outside,target_is_directory=True)
   before={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
   with self.assertRaises(ValueError):install.install(root,profile,{'modules':[],'findings':[]},adopt_existing=True)
   self.assertEqual(before,{str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()})
 def test_owned_profile_without_methodology_is_migrated_without_repeating_initial_choice(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'pom.xml').write_text('<project/>');execute(root,approved=True,methodology='odd')
   profile=root/'.harness/project-profile.json';data=json.loads(profile.read_text());data['decisions'].pop('methodology');profile.write_text(json.dumps(data))
   answers=root/'.aikya/answers.json';raw=json.loads(answers.read_text());raw.pop('methodology');answers.write_text(json.dumps(raw))
   result=execute(root,approved=True,refresh=True);self.assertEqual('READY',result['status']);self.assertEqual('odd',json.loads(profile.read_text())['decisions']['methodology'])
   self.assertNotIn('methodology',json.loads((root/'.harness/backup-odd/project-profile.json').read_text())['decisions'])
 def test_owned_legacy_answers_are_normalized_with_profile_and_backed_up(self):
  from aikya.workflows.methodology import migration_plan,apply_migration
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);previous={'_generated_by':'claude-dev-harness-interactive','decisions':{'methodology':'standard','project_type':'development','notes':'Keep'}}
   profile=root/'.harness/project-profile.json';profile.parent.mkdir();profile.write_text(json.dumps(previous));answers=root/'.aikya/answers.json';answers.parent.mkdir();answers.write_text(json.dumps(previous['decisions']))
   old=answers.read_bytes();operations=migration_plan(root,previous,'odd');self.assertTrue(operations);self.assertEqual(old,answers.read_bytes())
   apply_migration(root,operations);self.assertEqual('odd',json.loads(answers.read_text())['methodology']);self.assertEqual(old,(root/'.harness/backup-odd/answers.json').read_bytes());self.assertEqual('Keep',json.loads(answers.read_text())['notes'])
