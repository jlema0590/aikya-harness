"""Managed hooks run with their own Python and preserve shell argument boundaries."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ManagedHookCommands(unittest.TestCase):
    def renderer(self):
        try:
            return importlib.import_module('aikya.installation.hook_commands')
        except ModuleNotFoundError:
            self.fail('Managed cross-platform hook invocation is not implemented')

    def test_posix_hook_runs_without_python_on_path_with_quoted_paths(self):
        module = self.renderer()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "team's project"; root.mkdir()
            script = root / 'hook.py'; script.write_text('import json,sys;print(json.dumps(sys.argv[1:]))')
            record = module.render_managed_hook(Path(sys.executable), script, ('a b', "x'y", '$literal'), 'posix')
            process = subprocess.run(['/bin/sh', '-c', record['command']], env={**os.environ, 'PATH': ''}, capture_output=True, text=True)
            self.assertEqual(0, process.returncode, process.stderr)
            self.assertEqual(['a b', "x'y", '$literal'], json.loads(process.stdout))

    def test_powershell_uses_literal_arguments_and_explicit_shell(self):
        module = self.renderer()
        record = module.render_managed_hook(Path(sys.executable), Path('/project/aikya_session.py'), ("a'b", '$literal'), 'powershell')
        self.assertEqual('powershell', record['shell'])
        self.assertIn("'a''b'", record['command'])
        self.assertIn("'$literal'", record['command'])
        with self.assertRaises(ValueError):
            module.render_managed_hook(Path('relative/python'), Path('/script.py'), (), 'posix')
        with self.assertRaises(ValueError):
            module.render_managed_hook(Path(sys.executable), Path('/script.py'), (), 'unknown')

    def test_owned_quality_checks_use_managed_python_without_changing_user_commands(self):
        from aikya.tools import checks
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); script = root / 'aikya/scripts/harness/docs_guard.py'
            script.parent.mkdir(parents=True); script.write_text('raise SystemExit(0)')
            config = root / 'harness.json'; config.write_text(json.dumps({'checks': [{'name': 'docs:structure', 'command': ['python3', 'aikya/scripts/harness/docs_guard.py', 'base'], 'required': True}]}))
            with patch.object(checks, 'ROOT', root), patch.dict(os.environ, {'PATH': ''}):
                self.assertEqual(0, checks.run(config))

    def test_project_hook_translation_preserves_existing_timeout_policy(self):
        module = self.renderer()
        command = 'python3 "${CLAUDE_PROJECT_DIR}/.claude/hooks/stop_docs.py"'
        source = {'hooks': {'Stop': [{'hooks': [{'type': 'command', 'command': command},
                                               {'type': 'command', 'command': command, 'timeout': 97}]}]}}
        translated = module.project_settings(source, Path(tempfile.gettempdir()).resolve())
        hooks = translated['hooks']['Stop'][0]['hooks']
        self.assertNotIn('timeout', hooks[0])
        self.assertEqual(97, hooks[1]['timeout'])
