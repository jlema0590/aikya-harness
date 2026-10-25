"""Canonical names, real installed upgrades and conservative retirement."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aikya.installation import registration as aikya_setup
from aikya.middleware.commands import recipe
from aikya.documentation.composition import select
RENAMES={'aikya-project-init':'aikya-project','aikya-infra-project':'aikya-infra','aikya-architecture-review':'aikya-arc-review','aikya-documentation-sync':'aikya-docs-sync','aikya-skills-install':'aikya-install-skill'}
class CommandRenameTests(unittest.TestCase):
 def test_new_names_are_executable_recipes_and_old_names_are_not_registered(self):
  for old,new in RENAMES.items():
   self.assertIn(new,aikya_setup.BOOTSTRAP_COMMANDS)
   self.assertEqual(new,recipe(new)['command'])
   with self.assertRaises(ValueError):recipe(old)
  self.assertTrue(recipe('aikya-arc-review')['read_only'])
  self.assertNotIn('implement',recipe('aikya-arc-review')['required'])
  self.assertEqual('read_only',select({'project_type':'development','methodology':'odd'},'aikya-arc-review')['mode'])
 def test_upgrade_retires_verified_commands_with_backups_in_both_scopes(self):
  for scope in ('global','project'):
   with self.subTest(scope=scope),tempfile.TemporaryDirectory() as tmp:
    base=Path(tmp);root=base/'project';home=base/'home';aikya_setup.setup(ROOT,root,scope,home=home)
    skills=(home if scope=='global' else root)/'.claude/skills'
    runtime=home/'.claude/aikya-harnes' if scope=='global' else root/'.aikya/runtime'
    originals={}
    for old in RENAMES:
     path=skills/old/'SKILL.md';path.parent.mkdir(parents=True,exist_ok=True);raw=(ROOT/'tests/fixtures/command-renames'/(old+'.md')).read_bytes();path.write_bytes(raw);originals[old]=raw
    aikya_setup.setup(ROOT,root,scope,home=home)
    for old,new in RENAMES.items():
     self.assertFalse((skills/old/'SKILL.md').exists(),old);self.assertTrue((skills/new/'SKILL.md').is_file())
     self.assertEqual(originals[old],(runtime/'command-backups'/old/'SKILL.md').read_bytes())
    self.assertEqual(27,len(list(skills.glob('aikya-*/SKILL.md'))))
    before={p.relative_to(skills).as_posix():p.read_bytes() for p in skills.rglob('SKILL.md')}
    aikya_setup.setup(ROOT,root,scope,home=home)
    self.assertEqual(before,{p.relative_to(skills).as_posix():p.read_bytes() for p in skills.rglob('SKILL.md')})
 def test_project_installer_never_recreates_the_retired_public_aliases(self):
  from aikya.installation import facade as install
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);raw=json.loads((ROOT/'examples/next-react/answers.json').read_text());profile=install.validated(raw,root)
   install.install(root,profile,{'modules':[],'findings':[]},docs_lang='en')
   for old in RENAMES:self.assertFalse((root/'.claude/skills'/old/'SKILL.md').exists(),old)
   old=root/'.claude/skills/aikya-project-init/SKILL.md';old.parent.mkdir(exist_ok=True);old.write_bytes((ROOT/'tests/fixtures/command-renames/aikya-project-init.md').read_bytes())
   install.install(root,profile,{'modules':[],'findings':[]},docs_lang='en')
   self.assertFalse(old.exists());self.assertTrue((root/'.harness/command-backups/aikya-project-init/SKILL.md').is_file())
 def test_custom_old_command_is_preserved_and_reported_for_review(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);aikya_setup.setup(ROOT,root,'project');old=root/'.claude/skills/aikya-skills-install/SKILL.md';old.parent.mkdir(exist_ok=True);old.write_text('Team customized installation workflow\n')
   copied=root/'.aikya/runtime/bootstrap_skills/aikya-skills-install/SKILL.md';copied.parent.mkdir(parents=True);copied.write_bytes(old.read_bytes())
   logs=aikya_setup.setup(ROOT,root,'project');self.assertEqual('Team customized installation workflow\n',old.read_text());self.assertTrue(any('aikya-skills-install' in line and 'PRESERVED' in line for line in logs))
 def test_blocked_replacement_keeps_the_previous_command_active_in_both_scopes(self):
  for scope in ('global','project'):
   with self.subTest(scope=scope),tempfile.TemporaryDirectory() as tmp:
    base=Path(tmp);root=base/'project';home=base/'home';aikya_setup.setup(ROOT,root,scope,home=home)
    skills=(home if scope=='global' else root)/'.claude/skills'
    old=skills/'aikya-project-init/SKILL.md';old.parent.mkdir();raw=(ROOT/'tests/fixtures/command-renames/aikya-project-init.md').read_bytes();old.write_bytes(raw)
    replacement=skills/'aikya-project';(replacement/'SKILL.md').unlink();replacement.rmdir()
    outside=base/'outside';outside.mkdir();replacement.symlink_to(outside,target_is_directory=True)
    with self.assertRaises(ValueError):aikya_setup.setup(ROOT,root,scope,home=home)
    self.assertTrue(old.is_file(),'The old command must remain active until its replacement is available')
    self.assertEqual(raw,old.read_bytes());self.assertEqual([],list(outside.iterdir()))
 def test_unsafe_retirement_backup_is_rejected_without_removing_the_old_command(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'project';outside=Path(tmp)/'outside';outside.mkdir();aikya_setup.setup(ROOT,root,'project')
   old=root/'.claude/skills/aikya-project-init/SKILL.md';old.parent.mkdir(exist_ok=True);raw=(ROOT/'tests/fixtures/command-renames/aikya-project-init.md').read_bytes();old.write_bytes(raw)
   (root/'.aikya/runtime/command-backups').symlink_to(outside,target_is_directory=True)
   with self.assertRaises(ValueError):aikya_setup.setup(ROOT,root,'project')
   self.assertEqual(raw,old.read_bytes());self.assertEqual([],list(outside.iterdir()))
if __name__=='__main__':unittest.main()
