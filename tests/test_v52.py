"""v5.2: comandos públicos, instalación selectiva y documentación de skills."""
import runtime_support
from pathlib import Path
from unittest.mock import patch
import json
import shutil
import subprocess
import tempfile
import unittest
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aikya.installation import registration as aikya_setup
from aikya.installation import facade as install
from aikya.catalogs import external as ext
from aikya.catalogs.skills import render,write_inventory

class V52(unittest.TestCase):
    def test_new_commands_and_removed_source_aliases(self):
        expected={'aikya-infra','aikya-skills-status','aikya-skills-plan','aikya-install-skill'}
        self.assertTrue(expected.issubset(aikya_setup.BOOTSTRAP_COMMANDS))
        self.assertFalse({'aikya-project-bootstrap','aikya-skills'} & set(aikya_setup.BOOTSTRAP_COMMANDS))
        for name in expected:
            body=(ROOT/'src/aikya/resources/commands'/name/'SKILL.md').read_text()
            self.assertIn(f'name: {name}\n',body)
            self.assertIn('AIKYA BOOTSTRAP MANAGED',body)

    def test_new_init_generates_complete_skills_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            p=install.validated(json.loads((ROOT/'examples/new-next-react.json').read_text()),root)
            install.install(root,p,{'modules':[]})
            inv=(root/'aikya/docs/skills.md').read_text()
            self.assertIn('aikya-infra',inv)
            self.assertIn('aikya-install-skill',inv)
            self.assertIn('aikya-feature',inv)
            self.assertIn('not a history of model invocations',inv.lower())
            self.assertIn('skills.md',(root/'aikya/docs/indice.md').read_text())
            self.assertFalse((root/'.claude/skills/aikya-project-bootstrap').exists())
            self.assertFalse((root/'.claude/skills/aikya-skills').exists())
            self.assertTrue((root/'aikya/scripts/harness/skills_registry.py').is_file())
            r=subprocess.run([sys.executable,str(root/'aikya/scripts/harness/docs_guard.py'),'base'],cwd=root,capture_output=True,text=True)
            self.assertEqual(0,r.returncode,r.stderr)

    def test_inventory_preserves_user_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'docs').mkdir()
            (root/'aikya/docs').mkdir(parents=True,exist_ok=True)
            (root/'aikya/docs/skills.md').write_text('Documento de equipo\n')
            ok,note=write_inventory(root)
            self.assertFalse(ok)
            self.assertIn('personalizado',note)
            self.assertEqual('Documento de equipo\n',(root/'aikya/docs/skills.md').read_text())

    def test_selected_install_updates_inventory_without_others(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'.claude/skills').mkdir(parents=True)
            decisions={'backend':'java','frontend':'react','mobile':'none'}
            def ponytail(r):
                folder=r/'.claude/skills/ponytail'; folder.mkdir()
                (folder/'SKILL.md').write_text('---\nname: ponytail\ndescription: Check\n---\n')
                return {'state':'installed','source':'https://github.com/DietrichGebert/ponytail.git'}
            with patch.dict(ext.INSTALLERS,{'ponytail':ponytail,'graphify':lambda _:self.fail('Graphify NO seleccionado')}):
                record=ext.install_all(root,decisions,permission=True,selected=['ponytail'])
            self.assertEqual({'ponytail'},set(record['skills']))
            self.assertIn('https://github.com/DietrichGebert/ponytail.git',(root/'aikya/docs/skills.md').read_text())
            self.assertIn('ponytail',render(root))

    def test_custom_skill_github_fixture_no_network(self):
        if not shutil.which('git'):self.skipTest('git ausente')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'project';root.mkdir()
            source=Path(tmp)/'mockup';source.mkdir()
            child=source/'skills/example';child.mkdir(parents=True)
            (child/'SKILL.md').write_text('---\nname: example\ndescription: Example testing skill\n---\n# Example\n')
            for args in (['init','-q'],['add','.'],['-c','user.email=test@example.com','-c','user.name=Tester','commit','-m','fixture','-q']):
                r=subprocess.run(['git','-C',str(source)]+args,capture_output=True,text=True)
                self.assertEqual(0,r.returncode,r.stderr)
            def fake_run(args,**kwargs):
                if len(args)>1 and args[:2]==['git','clone']:
                    return subprocess.run(['git','clone',str(source),args[-1]],capture_output=True,text=True)
                return ext.subprocess.run(args,capture_output=True,text=True,cwd=str(kwargs['cwd']) if kwargs.get('cwd') else None)
            # To simulate remote cloning we rewrite the URL to our test repository.
            with patch.object(ext,'_invoke',side_effect=fake_run):
                result=ext.install_custom(root,{},name='example',repo='https://github.com/org/repo.git',skill_path='skills/example',permission=True)
            self.assertEqual('installed',result['skills']['example']['state'])
            self.assertTrue((root/'.claude/skills/example/SKILL.md').is_file())
            doc=(root/'aikya/docs/skills.md').read_text()
            self.assertIn('https://github.com/org/repo.git',doc)
            self.assertIn('/example',doc)
            with patch.object(ext,'_invoke',side_effect=lambda *a,**k:self.fail('No sobrescribir / clonar')):
                again=ext.install_custom(root,{},name='example',repo='https://github.com/org/repo.git',skill_path='skills/example',permission=True)
            self.assertEqual('failed',again['skills']['example']['state'])
            self.assertTrue((root/'.claude/skills/example/SKILL.md').is_file())

    def test_custom_source_rejection_no_clone(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            scenarios=[('bad name','https://github.com/org/repo','some/path'),('demo','https://evil.example/repo','x'),('demo','https://github.com/org/repo','../outside')]
            for name,repo,path in scenarios:
                with self.subTest(name=name,repo=repo,path=path),patch.object(ext,'_invoke') as m:
                    with self.assertRaises(ValueError):
                        ext.install_github_skill(root,name=name,repo=repo,skill_path=path,ref=None,commit=None,permission=True)
                    m.assert_not_called()

    def test_permission_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PermissionError):
                ext.install_custom(Path(tmp),{},name='example',repo='https://github.com/org/repo',skill_path='skill',permission=False)
            self.assertFalse((Path(tmp)/'docs').exists())

    def test_bootstrap_migration_retire_only_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'app'
            aikya_setup.setup(ROOT,root,'project')
            runtime=root/'.aikya/runtime'
            for old in ('aikya-skills','aikya-project-bootstrap'):
                # Self-contained legacy fixture; no dependency on an earlier checkout.
                legacy_content=('---\nname: '+old+'\ndescription: Legacy command\n---\n'
                                '<!-- AIKYA BOOTSTRAP MANAGED -->\n').encode('utf-8')
                legacy=root/'.claude/skills'/old/'SKILL.md';legacy.parent.mkdir(parents=True)
                legacy.write_bytes(legacy_content)
                rt=runtime/'bootstrap_skills'/old/'SKILL.md';rt.parent.mkdir(parents=True)
                rt.write_bytes(legacy_content)
            custom=root/'.claude/skills/aikya-skills/SKILL.md'
            custom.write_text(custom.read_text()+'\n# Personalizado\n')
            log=aikya_setup.setup(ROOT,root,'project')
            self.assertTrue(custom.exists())
            self.assertFalse((root/'.claude/skills/aikya-project-bootstrap').exists())
            self.assertTrue(any('RETIRADO' in x for x in log))
            self.assertTrue((root/'.claude/skills/aikya-infra/SKILL.md').is_file())

    def test_skill_docs_required_for_skill_changes(self):
        import importlib.util
        path=ROOT/'src/aikya/resources/project_template/scripts/harness/docs_guard.py'
        spec=runtime_support.module_spec('aikya_guard_skills',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module=getattr(module,'_module',module)
        self.assertTrue(module.is_source('.claude/skills/new-skill/SKILL.md'))
        self.assertIn('aikya/docs/skills.md',module.affected_docs('feature',['.claude/skills/new-skill/SKILL.md']))
        self.assertNotIn('aikya/docs/skills.md',module.DOCS_REQUIRED)

if __name__=='__main__': unittest.main()
