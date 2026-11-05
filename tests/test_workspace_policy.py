"""Native hook decisions, with no worktree creation or model invocation."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class WorkspacePolicyTests(unittest.TestCase):
    def decision(self, tool, data):
        run = subprocess.run([sys.executable, '-m', 'aikya.middleware.workspace'],
                             input=json.dumps({'tool_name': tool, 'tool_input': data}),
                             capture_output=True, text=True)
        self.assertEqual(0, run.returncode, run.stderr)
        return json.loads(run.stdout) if run.stdout.strip() else None

    def test_worktree_creation_requires_explicit_host_permission(self):
        for tool, data in [('EnterWorktree', {}), ('Agent', {'isolation': 'worktree'}),
                           ('Task', {'isolation': 'worktree'}),
                           ('Bash', {'command': 'git worktree add ../other'}),
                           ('Bash', {'command': 'cd repo && git -C "path with spaces" worktree add ../other'}),
                           ('PowerShell', {'command': "& git.exe worktree add '..\\other'"}),
                           ('Bash', {'command': 'claude --worktree feature'}),
                           ('Bash', {'command': 'claude -w feature'})]:
            with self.subTest(tool=tool, data=data):
                result = self.decision(tool, data)
                self.assertEqual('ask', result['hookSpecificOutput']['permissionDecision'])

    def test_ordinary_changes_branches_and_queries_are_unchanged(self):
        for tool, data in [('Edit', {'file_path': 'app.py'}), ('Agent', {'prompt': 'fix a label'}),
                           ('Bash', {'command': 'git switch -c fix/label'}),
                           ('Bash', {'command': 'git worktree list'}),
                           ('Bash', {'command': 'git worktree prune --dry-run'}),
                           ('Bash', {'command': "echo 'git worktree add ../example'"})]:
            with self.subTest(tool=tool, data=data):
                self.assertIsNone(self.decision(tool, data))

    def test_installed_hook_is_executable_and_preserves_custom_settings(self):
        from aikya.installation.registration import setup
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder).resolve(); home = base / 'home'; home.mkdir()
            config = home / '.claude/settings.json'; config.parent.mkdir()
            custom = {'type': 'command', 'command': 'echo custom'}
            config.write_text(json.dumps({'model': 'opus', 'hooks': {'PreToolUse': [{'hooks': [custom]}]}}))
            root = Path(__file__).resolve().parents[1]
            setup(root, base / 'project', 'global', home=home)
            settings = json.loads(config.read_text())
            self.assertEqual('opus', settings['model'])
            self.assertIn({'hooks': [custom]}, settings['hooks']['PreToolUse'])
            hooks = [h for g in settings['hooks']['PreToolUse'] for h in g['hooks']
                     if 'workspace_guard.py' in h.get('command', '')]
            self.assertEqual(1, len(hooks))
            result = subprocess.run([sys.executable, '-B', str(home / '.claude/aikya-harnes/workspace_guard.py')],
                                    input=json.dumps({'tool_name': 'Agent', 'tool_input': {'isolation': 'worktree'}}),
                                    capture_output=True, text=True, cwd=base)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual('ask', json.loads(result.stdout)['hookSpecificOutput']['permissionDecision'])
            before = config.read_bytes()
            setup(root, base / 'project', 'global', home=home)
            self.assertEqual(before, config.read_bytes())


if __name__ == '__main__':
    unittest.main()
