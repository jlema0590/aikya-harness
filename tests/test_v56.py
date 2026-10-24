"""Acceptance tests v5.6: repository topology, unified workspace and welcome."""
import runtime_support
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import contextlib
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT))
from aikya.installation import facade as install
from aikya.documentation import bootstrap as doc_bootstrap
from aikya.cli import session as aikya_session
from aikya.discovery.layout import app_count

def load_module(file, name):
    spec=runtime_support.module_spec(name, file)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod);mod=getattr(mod,'_module',mod)
    return getattr(mod, '_module', mod)

SCAFFOLD=load_module(ROOT/'src/aikya/resources/project_template/scripts/harness/scaffold.py','scaffold_v56')

class AikyaLayoutTests(unittest.TestCase):
    def answers(self, target, **changes):
        defaults={'name':'demo-app','mode':'new','backend':'next','backend_framework':'next-app-router',
                  'frontend':'react','mobile':'none','repository_layout':'singlerepo'}
        return install.validated({**defaults,**changes},target)

    def test_single_next_is_one_app_and_root_scaffold(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.answers(Path(d))
            self.assertEqual(1,app_count(p))
            commands,manual=SCAFFOLD.command_plans(p)
            self.assertEqual(['.'],[x['creates'] for x in commands])
            self.assertEqual([],manual)

    def test_single_rejects_independent_backend_frontend(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'monorepo'):
                self.answers(Path(d),backend='java',backend_framework='spring-boot',
                             frontend='react',repository_layout='singlerepo')

    def test_install_single_layout_has_no_workspaces_and_unified_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            p=self.answers(root)
            install.install(root,p,{'modules':[],'findings':[]})
            for rel in ('aikya/docs/README.md','aikya/docs/skills.md',
                        'aikya/test/test_harness.py','aikya/scripts/harness/scaffold.py',
                        '.claude/hooks/welcome.py'):
                self.assertTrue((root/rel).is_file(), rel)
            for rel in ('apps','packages','contracts','package.json','pnpm-workspace.yaml','docs','scripts'):
                self.assertFalse((root/rel).exists(),rel)
            self.assertEqual([],load_module(root/'aikya/scripts/harness/docs_guard.py','installed_guard').validate_base())
            self.assertTrue(any('aikya/scripts/harness/docs_guard.py' in str(x['command'])
                                for x in json.loads((root/'harness.json').read_text())['checks']))

    def test_monorepo_builds_directories(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            p=self.answers(root,repository_layout='monorepo')
            install.install(root,p,{'modules':[],'findings':[]})
            for path in ('apps/README.md','packages/README.md','contracts/README.md',
                         'aikya/docs/README.md','aikya/test/test_harness.py'):
                self.assertTrue((root/path).is_file(),path)
            self.assertTrue((root/'package.json').is_file())

    def test_preexisting_docs_are_copied_not_deleted(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            old=root/'docs/overview.md'
            old.parent.mkdir()
            old.write_text('# Documento editado por el equipo\n\nAlcance confirmado por el equipo.\n')
            p=self.answers(root,mode='existing')
            install.install(root,p,{'modules':[],'findings':[]})
            self.assertIn(old.read_text().strip(),(root/'aikya/docs/overview.md').read_text())
            self.assertEqual('# Documento editado por el equipo\n\nAlcance confirmado por el equipo.\n',old.read_text())
            self.assertTrue(old.exists())

    def test_single_scaffold_stages_and_preserves_ignore(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            p=self.answers(root)
            install.install(root,p,{'modules':[],'findings':[]})
            def fake_runner(command,cwd,**kwargs):
                stage=Path(cwd)
                (stage/'app').mkdir()
                (stage/'app/page.tsx').write_text('export default function Page(){return null}')
                (stage/'.gitignore').write_text('node_modules/\n.next/\n')
                return SimpleNamespace(returncode=0)
            with patch.object(SCAFFOLD.shutil,'which',return_value='/bin/mock'), patch('aikya.installation.requirements.check', return_value={'ready':True,'checks':[]}):
                # El detector se importa desde una ruta distinta: sustituir temporalmente su check local.
                script=root/'aikya/scripts/harness/aikya_requirements.py'
                original=script.read_bytes()
                try:
                    script.write_text('def check(profile, root):\n    return {"ready": True, "checks": []}\n')
                    result=SCAFFOLD.apply(p,root,True,runner=fake_runner)
                finally:
                    script.write_bytes(original)
            self.assertEqual(0,result)
            self.assertTrue((root/'app/page.tsx').is_file())
            self.assertTrue((root/'aikya/docs/README.md').is_file())
            self.assertIn('node_modules/',(root/'.gitignore').read_text())
            self.assertFalse((root/'apps').exists())

    def test_single_scaffold_aborts_before_copy_on_conflict(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            p=self.answers(root)
            install.install(root,p,{'modules':[],'findings':[]})
            path=root/'app/page.tsx'
            path.parent.mkdir()
            path.write_text('ORIGINAL')
            def fake_runner(cmd,cwd,**kwargs):
                stage=Path(cwd)
                (stage/'app').mkdir()
                (stage/'app/page.tsx').write_text('NUEVO')
                return SimpleNamespace(returncode=0)
            script=root/'aikya/scripts/harness/aikya_requirements.py'
            original=script.read_bytes()
            try:
                script.write_text('def check(profile, root):\n    return {"ready": True, "checks": []}\n')
                with patch.object(SCAFFOLD.shutil,'which',return_value='/bin/mock'):
                    result=SCAFFOLD.apply(p,root,True,runner=fake_runner)
            finally:
                script.write_bytes(original)
            self.assertEqual(2,result)
            self.assertEqual('ORIGINAL',path.read_text())

    def test_global_hook_greets_existing_project_without_local_hook(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'project'
            (root/'.harness').mkdir(parents=True)
            (root/'.harness/project-profile.json').write_text('{}')
            event=json.dumps({'source':'startup','cwd':str(root)})
            out=io.StringIO()
            with patch('sys.stdin',io.StringIO(event)),contextlib.redirect_stdout(out):
                code=aikya_session.main()
            self.assertEqual(0,code)
            self.assertIn('Welcome to Aikya Harness',json.loads(out.getvalue())['systemMessage'])

    def test_migrate_only_original_v55_hooks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            hooks=root/'.claude/hooks'
            hooks.mkdir(parents=True)
            previous=ROOT/'src/aikya/resources/migrations/v55/hooks/request_docs.py'
            (hooks/'request_docs.py').write_bytes(previous.read_bytes())
            custom=(hooks/'stop_docs.py')
            custom.write_text('#!/usr/bin/env python3\n# custom team hook\n')
            p=self.answers(root,mode='existing')
            install.install(root,p,{'modules':[],'findings':[]})
            self.assertEqual((ROOT/'src/aikya/resources/project_template/.claude/hooks/request_docs.py').read_bytes(),
                             (hooks/'request_docs.py').read_bytes())
            self.assertIn('custom team hook',custom.read_text())

    def test_migrate_default_quality_check_paths_without_touching_user_check(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            checks={'schema_version':2,'checks':[
                {'name':'docs:structure','command':['python3','scripts/harness/docs_guard.py','base'],'cwd':'.','required':True},
                {'name':'skills:format','command':['python3','scripts/harness/skills_lint.py'],'cwd':'.','required':True},
                {'name':'custom:lint','command':['npm','run','lint'],'cwd':'.','required':True}]}
            (root/'harness.json').write_text(json.dumps(checks))
            p=self.answers(root,mode='existing')
            install.install(root,p,{'modules':[],'findings':[]})
            actual=json.loads((root/'harness.json').read_text())['checks']
            self.assertEqual('aikya/scripts/harness/docs_guard.py',actual[0]['command'][1])
            self.assertEqual('aikya/scripts/harness/skills_lint.py',actual[1]['command'][1])
            self.assertEqual(['npm','run','lint'],actual[2]['command'])

if __name__=='__main__':
    unittest.main()
