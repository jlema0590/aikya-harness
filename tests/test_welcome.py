"""La bienvenida debe ser segura, reproducible y compatible con SessionStart."""
import runtime_support
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from aikya.installation import facade as install

SCRIPT = BASE / 'src/aikya/resources/project_template/.claude/hooks/welcome.py'
spec = runtime_support.module_spec('aikya_welcome', SCRIPT)
welcome = importlib.util.module_from_spec(spec)
spec.loader.exec_module(welcome);welcome=getattr(welcome,'_module',welcome)


class WelcomeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / '.harness').mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self, source='startup'):
        env = {**os.environ, 'CLAUDE_PROJECT_DIR': str(self.root)}
        env.pop('AIKYA_DISPLAY_NAME', None)
        result = subprocess.run([sys.executable, str(SCRIPT)],
            input=json.dumps({'source':source}), capture_output=True, text=True, env=env, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_welcome_system_message_includes_name_repo_and_source(self):
        (self.root/'.harness/welcome.json').write_text(json.dumps({'display_name':'Juan'}))
        with patch.object(welcome, 'git_value', side_effect=lambda r,*args: 'git@github.com:team/mi-api.git' if args[0]=='remote' else ''):
            self.assertIn('team/mi-api', welcome.build_message(self.root))
        payload=json.loads(self.invoke())
        self.assertEqual(list(payload),['systemMessage'])
        self.assertIn('Juan',payload['systemMessage'])
        self.assertIn('github.com/jlema0590/aikya-harnes',payload['systemMessage'])

    def test_no_duplicate_after_clear_or_compact(self):
        self.assertEqual(self.invoke('clear'),'')
        self.assertEqual(self.invoke('compact'),'')
        self.assertIn('systemMessage', self.invoke('resume'))

    def test_unsafe_remote_never_exposes_secrets(self):
        self.assertEqual(welcome.safe_remote('https://user:TOKEN@github.com/team/repo.git'), 'team/repo')
        self.assertEqual(welcome.safe_remote('https://another.example/user:SECRET'), '')
        self.assertEqual(welcome.safe_remote('git@github.com:team/repo.git\nSECRET'), '')
        self.assertNotIn('TOKEN', welcome.safe_remote('https://user:TOKEN@github.com/team/repo.git'))

    def test_untrusted_identity_does_not_emit_controls(self):
        with patch.dict(os.environ, {'AIKYA_DISPLAY_NAME':'Ana\x1b[31m\nSECRETO'}, clear=False):
            val=welcome.identity(self.root)
        self.assertNotIn('\x1b',val)
        self.assertNotIn('\n',val)
        self.assertLessEqual(len(val),48)

    def test_install_generates_welcome_hook_and_settings(self):
        profile=install.validated({'backend':'java', 'backend_framework':'spring-boot',
                'mode':'existing'}, self.root)
        install.install(self.root,profile,{'modules':[],'findings':[]})
        self.assertTrue((self.root/'.claude/hooks/welcome.py').is_file())
        s=json.loads((self.root/'.claude/settings.json').read_text())
        self.assertTrue(any('welcome.py' in h.get('command','')
            for group in s['hooks']['SessionStart'] for h in group['hooks']))

    def test_merge_existing_session_start_preserves_other_hooks_and_idempotent(self):
        setting=self.root/'.claude/settings.json'
        setting.parent.mkdir(parents=True)
        setting.write_text(json.dumps({'hooks':{'SessionStart':[{'hooks':[{'type':'command','command':'echo PREEXISTENTE'}]}]}}))
        actions=[]
        install.merge_settings(self.root,actions)
        first=json.loads(setting.read_text())
        self.assertTrue(any('PREEXISTENTE' in str(g) for g in first['hooks']['SessionStart']))
        self.assertTrue(any('welcome.py' in str(g) for g in first['hooks']['SessionStart']))
        install.merge_settings(self.root,[])
        self.assertEqual(first,json.loads(setting.read_text()))

    def test_cli_display_name_stored_locally_not_in_shared_profile(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'project'
            cmd=[sys.executable,str(BASE/'install.py'),'--target',str(root),
                 '--answers',str(BASE/'examples/new-next-react.json'),
                 '--external','skip','--display-name','Juan']
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads((root/'.harness/welcome.json').read_text())['display_name'],'Juan')
            self.assertNotIn('Juan',(root/'.harness/project-profile.json').read_text())
            self.assertIn('.harness/welcome.json',(root/'.gitignore').read_text())
            preview=subprocess.run([sys.executable,str(root/'.claude/hooks/welcome.py'),'--preview'],
                text=True,capture_output=True,cwd=root,timeout=5)
            self.assertIn('Juan',preview.stdout)
            self.assertEqual(preview.returncode,0)

    def test_root_repo_has_startup_hook(self):
        cfg=json.loads((BASE/'.claude/settings.json').read_text())
        self.assertIn('template/.claude/hooks/welcome.py',str(cfg))


if __name__=='__main__':
    unittest.main()
