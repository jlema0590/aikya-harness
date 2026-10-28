"""Flow's invocation identity survives CLI processes, worktrees and parallel runs."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from aikya.core import state
from aikya.middleware.lifecycle import Lifecycle

ROOT = Path(__file__).resolve().parents[1]

class FlowBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / 'project'
        self.root.mkdir()
        self.worktree = self.root / '.claude/worktrees/analysis'
        self.worktree.mkdir(parents=True)
        self.cache = self.base / 'cache'
        self.bridge = {'schema': 1, 'origin_root': str(self.root), 'session_id': 'claude-real-session',
                       'invocation_id': 'a' * 32, 'command': 'aikya-analyze', 'cache_root': str(self.cache)}
        self.env = {'AIKYA_EXECUTION_CACHE': str(self.cache), 'AIKYA_FLOW_CONTEXT': json.dumps(self.bridge)}
        self.patch = patch.dict(os.environ, self.env)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def index(self):
        identity = hashlib.sha256((str(self.root) + '\0claude-real-session').encode()).hexdigest()
        return json.loads((self.cache / identity / ('flow-' + 'a' * 32 + '.json')).read_text())

    def test_cli_in_worktree_uses_real_session_and_publishes_correlated_reference(self):
        lifecycle = Lifecycle(self.worktree, 'local', 'aikya-analyze', preview=True)
        self.assertEqual('claude-real-session', lifecycle.context['session_id'])
        value = state.read_active(lifecycle.context)
        self.assertEqual('a' * 32, value['flow_invocation'])
        self.assertEqual('skipped', value['phases']['implement']['status'])
        index = self.index()
        self.assertEqual('claude-real-session', index['session_id'])
        self.assertEqual(value['identity'], index['runs'][0]['identity'])
        self.assertEqual(value['run_id'], index['runs'][0]['run_id'])
        self.assertEqual('preview', index['runs'][0]['mode'])

    def test_parallel_worktrees_keep_independent_snapshots_under_one_invocation(self):
        other = self.root / '.claude/worktrees/security'
        other.mkdir()
        with ThreadPoolExecutor(max_workers=2) as pool:
            runs = list(pool.map(lambda root: Lifecycle(root, 'local', 'aikya-analyze', preview=True), [self.worktree, other]))
        index = self.index()
        self.assertEqual(2, len(index['runs']))
        self.assertEqual(2, len({row['identity'] for row in index['runs']}))
        self.assertEqual({item.context['run_id'] for item in runs}, {row['run_id'] for row in index['runs']})

    def test_foreign_session_does_not_publish_into_the_claude_invocation(self):
        lifecycle = Lifecycle(self.worktree, 'another-session', 'aikya-analyze', preview=True)
        self.assertEqual('another-session', lifecycle.context['session_id'])
        self.assertNotIn('flow_invocation', state.read_active(lifecycle.context))
        self.assertEqual([], list(self.cache.glob('*/flow-*.json')))

    def test_unrelated_target_and_malformed_context_are_not_adopted(self):
        unrelated = self.base / 'unrelated'
        unrelated.mkdir()
        lifecycle = Lifecycle(unrelated, 'local', 'aikya-analyze', preview=True)
        self.assertEqual('local', lifecycle.context['session_id'])
        for value in ['{', json.dumps({**self.bridge, 'invocation_id': '../escape'}),
                      json.dumps({**self.bridge, 'session_id': 'local'})]:
            with patch.dict(os.environ, {'AIKYA_FLOW_CONTEXT': value}):
                lifecycle = Lifecycle(self.worktree, 'local', 'aikya-analyze', preview=True)
                self.assertEqual('local', lifecycle.context['session_id'])
        self.assertEqual([], list(self.cache.glob('*/flow-*.json')))

    def test_real_cli_records_focus_without_explicit_session_or_project_writes(self):
        (self.worktree / 'pom.xml').write_text('<project/>')
        before = sorted(str(path.relative_to(self.worktree)) for path in self.worktree.rglob('*'))
        env = {**os.environ, 'PYTHONPATH': str(ROOT / 'src'), 'PYTHONDONTWRITEBYTECODE': '1'}
        env.pop('CLAUDE_SESSION_ID', None)
        proc = subprocess.run([sys.executable, '-B', '-m', 'aikya', 'analyze', '--target', str(self.worktree),
                               '--methodology', 'odd', '--focus', 'architecture', '--dry-run'],
                              env=env, capture_output=True, text=True)
        self.assertEqual(0, proc.returncode, proc.stderr)
        row = self.index()['runs'][0]
        self.assertEqual('architecture', row['focus'])
        raw = state.read_snapshot({'root': str(self.worktree), 'session_id': 'claude-real-session',
                                   'cache_root': str(self.cache), 'run_id': row['run_id']})
        self.assertEqual('completed', raw['status'])
        self.assertEqual('skipped', raw['phases']['implement']['status'])
        self.assertEqual(before, sorted(str(path.relative_to(self.worktree)) for path in self.worktree.rglob('*')))

    def test_hook_and_child_cli_keep_one_correlated_execution(self):
        from aikya.middleware.observer import observe
        context = {'root': str(self.worktree), 'session_id': 'claude-real-session', 'cache_root': str(self.cache)}
        run = observe(context, {'hook_event_name': 'UserPromptSubmit', 'prompt': '/aikya-analyze'})
        self.assertEqual('a' * 32, run.get('flow_invocation'))
        self.assertEqual(run['run_id'], self.index()['runs'][0]['run_id'])
        cli = Lifecycle(self.worktree, 'local', 'aikya-analyze', preview=True, focus='security')
        self.assertEqual(run['run_id'], cli.context['run_id'])
        self.assertEqual(1, len(self.index()['runs']))
        self.assertEqual('preview', self.index()['runs'][0]['mode'])
        self.assertEqual('security', self.index()['runs'][0]['focus'])

    def test_hook_failure_uses_the_correlated_session_after_background_execution(self):
        from aikya.middleware.observer import observe
        lifecycle = Lifecycle(self.worktree, 'local', 'aikya-analyze', preview=True)
        observe({'root': str(self.worktree), 'session_id': 'local', 'cache_root': str(self.cache)},
                {'hook_event_name': 'StopFailure'})
        self.assertEqual('interrupted', state.read_active(lifecycle.context)['status'])

    def test_malformed_index_never_aborts_the_cli_lifecycle(self):
        first = Lifecycle(self.worktree, 'local', 'aikya-analyze', preview=True)
        index = self.index()
        folder = state.directory({**first.context, 'root': str(self.root)})
        path = folder / ('flow-' + 'a' * 32 + '.json')
        index['runs'] = [None]
        path.write_text(json.dumps(index))
        second = Lifecycle(self.worktree, 'local', 'aikya-analyze', preview=True)
        self.assertTrue(second.enabled)
        self.assertNotEqual(first.context['run_id'], second.context['run_id'])
        self.assertEqual([None], json.loads(path.read_text())['runs'])

    def test_phase_cli_and_check_runner_use_inherited_flow_session(self):
        lifecycle = Lifecycle(self.worktree, 'local', 'aikya-analyze', preview=True)
        env = {**os.environ, 'PYTHONPATH': str(ROOT / 'src'), 'PYTHONDONTWRITEBYTECODE': '1'}
        env.pop('CLAUDE_SESSION_ID', None)
        result = subprocess.run([sys.executable, '-B', '-m', 'aikya.middleware.observer', 'phase',
                                 '--root', str(self.worktree), '--phase', 'plan', '--status', 'running'],
                                env=env, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        from aikya.middleware.events import CheckEvents
        with patch.dict(os.environ, {'CLAUDE_SESSION_ID': 'local'}):
            checks = CheckEvents(self.worktree)
            checks.process('real fixture check outcome', 0)
            checks.finish(0)
        raw = state.read_active(lifecycle.context)
        self.assertEqual('running', raw['phases']['plan']['status'])
        self.assertEqual('completed', raw['phases']['validate']['status'])


if __name__ == '__main__':
    unittest.main()
