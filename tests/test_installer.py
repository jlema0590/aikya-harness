import runtime_support
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = runtime_support.module_spec('harness_installer', ROOT / 'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer);installer=getattr(installer,'_module',installer)


def profile(**overrides):
    data = {'mode':'new', 'name':'mi-app', 'backend':'dotnet', 'frontend':'vue',
            'mobile':'both','mobile_framework':'native','android_language':'kotlin',
            'ios_ui':'swiftui','architecture':'modular-monolith','database':'postgresql',
            'ci':'github-actions','deployment':'docker','package_manager':'npm'}
    data.update(overrides)
    return data


class InstallerTests(unittest.TestCase):
    def test_detect_existing_node_react(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'apps/api').mkdir(parents=True)
            (root/'apps/web').mkdir(parents=True)
            (root/'apps/api/package.json').write_text(json.dumps({'dependencies':{'express':'*'},'scripts':{'test':'vitest run','lint':'eslint .'}}))
            (root/'apps/web/package.json').write_text(json.dumps({'dependencies':{'react':'*','vite':'*'},'scripts':{'build':'vite build'}}))
            detected=installer.detect_project(root)
            self.assertIn(('backend','node','apps/api'), {(m['role'],m['technology'],m['path']) for m in detected['modules']})
            self.assertIn(('frontend','react','apps/web'), {(m['role'],m['technology'],m['path']) for m in detected['modules']})
            checks=installer.make_checks(root,installer.validated(profile(mode='existing',backend='node',frontend='react'),root),detected['modules'])
            self.assertIn({'name':'backend:node:apps/api:test','command':['npm','run','test'],'cwd':'apps/api','required':True},checks)
            self.assertIn({'name':'frontend:react:apps/web:test','command':None,'cwd':'apps/web','required':True},checks)

    def test_existing_java_dotnet_android_ios_detection(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for p in ['backend','apps/api','android/app/src/main','ios']:
                (root/p).mkdir(parents=True)
            (root/'backend/pom.xml').write_text('<project/>')
            (root/'apps/api/A.csproj').write_text('<Project />')
            (root/'android/app/src/main/AndroidManifest.xml').write_text('<manifest/>')
            (root/'ios/MyApp.xcodeproj').mkdir()
            technologies={(m['role'],m['technology']) for m in installer.detect_project(root)['modules']}
            self.assertTrue({('backend','java'),('backend','dotnet'),('mobile','android'),('mobile','ios')}.issubset(technologies))

    def test_next_detected_once_for_checks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'package.json').write_text(json.dumps({'dependencies':{'next':'*','react':'*'},'scripts':{'test':'vitest run'}}))
            detected=installer.detect_project(root)
            prof=installer.validated(profile(mode='existing',backend='next',frontend='react',mobile='none'),root)
            checks=installer.make_checks(root,prof,detected['modules'])
            self.assertEqual(1, len([c for c in checks if c['name'].endswith(':test')]))

    def test_new_has_tests_not_configured(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'demo'
            prof=installer.validated(profile(),root)
            checks=installer.make_checks(root,prof,[])
            self.assertEqual(4,len([c for c in checks if c['required']]))  # backend, web, Android y iOS independientes
            self.assertTrue(all(c['command'] is None for c in checks))

    def test_mobile_native_validation_requires_framework(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                installer.validated(profile(mobile_framework='none'), Path(d))

    def test_incompatible_framework_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                installer.validated(profile(backend_framework='spring-boot'), Path(d))

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'newrepo'
            installer.install(target,installer.validated(profile(),target),{'modules':[],'findings':[]},dry_run=True)
            self.assertFalse(target.exists())

    def test_new_project_install_and_settings(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'newrepo'
            prof=installer.validated(profile(),target)
            actions=installer.install(target,prof,{'modules':[],'findings':[]})
            self.assertTrue((target/'.claude/agents/mobile-engineer.md').exists())
            self.assertTrue((target/'.claude/skills/project-init/SKILL.md').exists())
            self.assertIn('kotlin', (target/'.claude/rules/00-project-profile.md').read_text())
            self.assertIn('dotnet new webapi', (target/'aikya/docs/overview.md').read_text())
            self.assertIn('Vue', (target/'aikya/docs/overview.md').read_text())
            self.assertIn('Android', (target/'aikya/docs/overview.md').read_text())
            self.assertIn('iOS', (target/'aikya/docs/overview.md').read_text())
            self.assertTrue(any(x.startswith('CREADO') for x in actions))
            installed=json.loads((target/'.harness/project-profile.json').read_text())
            self.assertEqual('both', installed['decisions']['mobile'])
            self.assertTrue(json.loads((target/'.claude/settings.json').read_text())['hooks']['PreToolUse'])

    def test_existing_files_preserved_settings_fused_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)
            (target/'.claude').mkdir()
            (target/'CLAUDE.md').write_text('MI REGLA PRIVADA DEL REPO\n')
            (target/'harness.json').write_text('{"checks":[]}\n')
            (target/'.claude/settings.json').write_text(json.dumps({'permissions':{'deny':['Read(./private.txt)']},'hooks':{'PreToolUse':[{'matcher':'Bash','hooks':[{'type':'command','command':'echo user-hook'}]}]},'custom':{'feature':True}}))
            p=installer.validated(profile(mode='existing'),target)
            detected={'modules':[],'findings':[]}
            installer.install(target,p,detected)
            installer.install(target,p,detected)
            self.assertEqual('MI REGLA PRIVADA DEL REPO\n',(target/'CLAUDE.md').read_text())
            self.assertEqual('{"checks":[]}\n',(target/'harness.json').read_text())
            settings=json.loads((target/'.claude/settings.json').read_text())
            self.assertIn('Read(./private.txt)',settings['permissions']['deny'])
            self.assertTrue(settings['custom']['feature'])
            self.assertEqual(3,len(settings['hooks']['PreToolUse']))

    def test_runner_rejects_cwd_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            temp=Path(d)
            p=temp/'harness.json'
            p.write_text(json.dumps({'checks':[{'name':'bad','required':True,'cwd':'/etc','command':['python3','--version']}]}))
            # Runner lives in template and uses the template root, but config path is arbitrary.
            spec2=runtime_support.module_spec('r',ROOT/'src/aikya/resources/project_template/scripts/harness/run_checks.py')
            runner=importlib.util.module_from_spec(spec2)
            spec2.loader.exec_module(runner)
            self.assertEqual(1,runner.run(p))

    def test_example_cli_install(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'demo'
            proc=subprocess.run([sys.executable,str(ROOT / 'src/aikya/installation/facade.py'),'--target',str(root),'--answers',str(ROOT/'examples/new-fullstack-mobile.json')],capture_output=True,text=True)
            self.assertEqual(0,proc.returncode,proc.stderr)
            self.assertTrue((root/'.claude/settings.json').is_file())
            self.assertTrue((root/'.harness/project-profile.json').is_file())

    def test_cli_new_refuses_nonempty_target(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'README.md').write_text('existing project')
            proc=subprocess.run([sys.executable,str(ROOT / 'src/aikya/installation/facade.py'),'--target',str(root),'--answers',str(ROOT/'examples/new-next-react.json')],capture_output=True,text=True)
            self.assertEqual(2,proc.returncode)
            self.assertFalse((root/'.harness').exists())


if __name__ == '__main__':
    unittest.main()
