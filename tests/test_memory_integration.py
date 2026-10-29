"""Exercise public CLI and copied runtime assets instead of source-text checks."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import contextmanager
from unittest.mock import patch
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def completed_observers():
    """Wait for actual test-owned children before deleting their Windows cwd."""
    processes = []
    launch = subprocess.Popen

    def observed_launch(*args, **kwargs):
        process = launch(*args, **kwargs)
        processes.append(process)
        return process

    with patch('aikya.code_index.hooks.subprocess.Popen', side_effect=observed_launch):
        try:
            yield
        finally:
            for process in processes:
                try:
                    process.wait(12)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(5)
                    raise AssertionError('Session observer did not exit after SessionEnd')


class MemoryIntegrationTests(unittest.TestCase):
    def run_cli(self, root, *flags):
        return subprocess.run([sys.executable, '-B', '-m', 'aikya', 'memory', '--target', str(root), *flags],
                              capture_output=True, text=True, timeout=15)

    def test_public_command_exports_and_preview_is_read_only(self):
        from aikya.code_index.policy import configure
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve();configure(root, approved=True)
            (root / 'value.py').write_text('class Value: pass\n')
            preview = self.run_cli(root, '--dry-run')
            self.assertEqual(0, preview.returncode, preview.stderr)
            self.assertFalse((root / '.harness').exists())
            actual = self.run_cli(root, '--refresh')
            self.assertEqual(0, actual.returncode, actual.stderr)
            self.assertEqual('complete', json.loads(actual.stdout)['status'])
            invalid = self.run_cli(root, '--dry-run', '--watch')
            self.assertEqual(2, invalid.returncode)

    def test_copied_registration_has_command_and_offline_viewer_resources(self):
        from aikya.installation.registration import setup, BOOTSTRAP_COMMANDS
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve();setup(ROOT, root, 'project')
            self.assertIn('aikya-memory', BOOTSTRAP_COMMANDS)
            self.assertTrue((root / '.claude/skills/aikya-memory/SKILL.md').is_file())
            (root / 'value.py').write_text('class Value: pass\n')
            runtime = root / '.aikya/runtime'
            script = ('import sys;sys.path.insert(0,sys.argv[1]);'
                      'from pathlib import Path;from aikya.code_index.policy import configure;'
                      'from aikya.cli.main import main;configure(Path(sys.argv[2]),approved=True);'
                      'raise SystemExit(main(["memory","--target",sys.argv[2],"--refresh"]))')
            result = subprocess.run([sys.executable, '-I', '-B', '-c', script, str(runtime / 'src'), str(root)],
                                    text=True, capture_output=True, timeout=20)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn('Value', (root / 'aikya/docs/memory/view/index.html').read_text())

    def test_approved_onboarding_configures_local_memory_without_starting_loop(self):
        from aikya.installation import facade
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            profile = facade.validated(json.loads((ROOT / 'examples/next-react/answers.json').read_text()), root)
            facade.install(root, profile, {'modules': [], 'findings': []}, docs_lang='en')
            policy = json.loads((root / '.aikya/code-index.json').read_text())
            self.assertTrue(policy['watch'])
            self.assertTrue((root / 'aikya/docs/memory/view/index.html').is_file())
            self.assertFalse((root / 'aikya/docs/loops').exists())

    def test_session_hooks_start_and_stop_only_the_project_observer(self):
        from aikya.code_index.policy import configure
        from aikya.code_index.hooks import process_event
        with tempfile.TemporaryDirectory() as folder, completed_observers():
            root = Path(folder).resolve();configure(root, approved=True)
            (root / 'entity.py').write_text('class SessionEntity: pass\n')
            event = {'hook_event_name': 'SessionStart', 'session_id': 'test-session'}
            process_event(root, event)
            path = root / 'aikya/docs/memory/view/index.html'
            deadline = time.monotonic() + 10
            try:
                while not path.exists() and time.monotonic() < deadline:
                    time.sleep(.05)
                self.assertTrue(path.is_file(), 'Session observer did not create report')
                (root / 'new.py').write_text('class SessionNew: pass\n')
                deadline = time.monotonic() + 10
                while 'SessionNew' not in path.read_text() and time.monotonic() < deadline:
                    time.sleep(.05)
                self.assertIn('SessionNew', path.read_text())
            finally:
                process_event(root, {'hook_event_name': 'SessionEnd', 'session_id': 'test-session'})
                state = root / '.harness/state/memory-view/status.json'
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    if state.exists() and json.loads(state.read_text()).get('state') == 'Stopped':
                        break
                    time.sleep(.05)
                self.assertEqual('Stopped', json.loads(state.read_text())['state'])

    def test_loop_context_uses_index_only_inside_its_approved_files(self):
        from agent_loop_support import project, config, runtime
        from aikya.code_index.policy import configure
        from aikya.core.loop import run
        with tempfile.TemporaryDirectory() as folder:
            root = project(folder)
            configure(root, approved=True)
            (root / 'src/value.py').write_text('class Value: pass\nVALUE = 0\n')
            (root / 'outside.py').write_text('class ValueOutside: pass\n')
            delegate = runtime()
            prompts = []
            class ObservedRuntime:
                is_sdk = False
                def available(self):
                    return delegate.available()
                def execute(self, request, on_event, cancel):
                    prompts.append(request['prompt'])
                    return delegate.execute(request, on_event, cancel)
            result = run(root, config(), ObservedRuntime(), approved=True)
            self.assertEqual('completed', result['status'], result.get('reason'))
            prompt = prompts[0]
            self.assertIn('Verified bounded source', prompt)
            self.assertIn('class Value:', prompt)
            self.assertNotIn('ValueOutside', prompt)

    def test_custom_memory_outputs_block_onboarding_before_other_project_writes(self):
        from aikya.installation import facade
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            custom = root / 'aikya/docs/memory/view/index.html'
            custom.parent.mkdir(parents=True);custom.write_text('Team report')
            profile = facade.validated(json.loads((ROOT / 'examples/next-react/answers.json').read_text()), root)
            with self.assertRaises(ValueError):
                facade.install(root, profile, {'modules': [], 'findings': []}, docs_lang='en')
            self.assertFalse((root / '.harness/project-profile.json').exists())
            self.assertEqual('Team report', custom.read_text())

    def test_memory_command_records_real_local_phases_without_claiming_a_model(self):
        from aikya.code_index.policy import configure
        from aikya.core.state import read_active
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve();configure(root, approved=True)
            (root / 'entity.py').write_text('class Entity: pass\n')
            result = self.run_cli(root, '--refresh', '--session', 'memory-contract')
            self.assertEqual(0, result.returncode, result.stderr)
            state = read_active({'root': str(root), 'session_id': 'memory-contract'})
            self.assertIsNotNone(state)
            self.assertEqual('completed', state['status'])
            self.assertEqual('completed', state['phases']['validate']['status'])
            self.assertEqual('skipped', state['phases']['review']['status'])
            self.assertTrue(all(event['observed_model'] is None for event in state['history']))

    def test_session_observer_respects_disabled_automatic_export(self):
        from aikya.code_index.policy import configure
        from aikya.code_index.hooks import process_event
        with tempfile.TemporaryDirectory() as folder, completed_observers():
            root = Path(folder).resolve();configure(root, approved=True)
            path = root / '.aikya/code-index.json'
            policy = json.loads(path.read_text());policy['auto_export'] = False
            path.write_text(json.dumps(policy));(root / 'entity.py').write_text('class Entity: pass\n')
            process_event(root, {'hook_event_name': 'SessionStart', 'session_id': 'index-only'})
            try:
                deadline = time.monotonic() + 8
                while not (root / '.harness/state/code-index/index.sqlite').exists() and time.monotonic() < deadline:
                    time.sleep(.05)
                self.assertTrue((root / '.harness/state/code-index/index.sqlite').exists())
                self.assertFalse((root / 'aikya/docs/memory/view/index.html').exists())
            finally:
                process_event(root, {'hook_event_name': 'SessionEnd', 'session_id': 'index-only'})
                state = root / '.harness/state/memory-view/status.json'
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline and json.loads(state.read_text()).get('state') != 'Stopped':
                    time.sleep(.05)

    def test_onboarding_respects_existing_disabled_export_policy(self):
        from aikya.code_index.policy import configure
        from aikya.installation import facade
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve();configure(root, approved=True)
            path = root / '.aikya/code-index.json'
            policy = json.loads(path.read_text());policy['auto_export'] = False
            path.write_text(json.dumps(policy))
            profile = facade.validated(json.loads((ROOT / 'examples/next-react/answers.json').read_text()), root)
            facade.install(root, profile, {'modules': [], 'findings': []}, docs_lang='en')
            self.assertFalse((root / 'aikya/docs/memory/view/index.html').exists())

    def test_live_client_reuses_session_observer_and_releases_only_its_lease(self):
        from aikya.code_index.policy import configure
        from aikya.code_index.hooks import process_event
        with tempfile.TemporaryDirectory() as folder, completed_observers():
            root = Path(folder).resolve();configure(root, approved=True)
            (root / 'entity.py').write_text('class Entity: pass\n')
            process_event(root, {'hook_event_name': 'SessionStart', 'session_id': 'host-session'})
            state = root / '.harness/state/memory-view/status.json'
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if state.exists() and json.loads(state.read_text()).get('state') == 'Up to date':
                    break
                time.sleep(.05)
            observer = json.loads(state.read_text())['pid']
            script = '''import sys,time,threading,signal,webbrowser
from pathlib import Path
root=Path(sys.argv[2])
webbrowser.open=lambda url:(root/'viewer-url.txt').write_text(url)
def stop_when_requested():
    while not (root/'stop-viewer.txt').exists(): time.sleep(.05)
    signal.raise_signal(signal.SIGINT)
threading.Thread(target=stop_when_requested,daemon=True).start()
sys.path.insert(0,sys.argv[1])
from aikya.cli.main import main
raise SystemExit(main(['memory','--target',str(root),'--watch','--open','--docs-lang','es']))
'''
            client = subprocess.Popen([sys.executable, '-I', '-B', '-c', script, str(ROOT / 'src'), str(root)],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            try:
                # A loaded CI host can start later; readiness is the actual URL
                # published by the OS-browser callback, not a fixed sleep.
                ready_url = root / 'viewer-url.txt'
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline and client.poll() is None:
                    if ready_url.is_file() and ready_url.stat().st_size:
                        break
                    time.sleep(.05)
                self.assertIsNone(client.poll(), 'Live client stopped instead of reusing the running observer')
                self.assertTrue(ready_url.is_file(), 'Live client did not publish its ready URL')
                with urlopen(ready_url.read_text(encoding='utf8'), timeout=5) as response:
                    self.assertIn('<html lang="es"', response.read().decode())
                self.assertEqual(observer, json.loads(state.read_text())['pid'])
                (root / 'stop-viewer.txt').write_text('stop')
                self.assertEqual(0, client.wait(10))
                self.assertNotEqual('Stopped', json.loads(state.read_text())['state'])
            finally:
                (root / 'stop-viewer.txt').write_text('stop')
                if client.poll() is None:
                    try:client.wait(10)
                    except subprocess.TimeoutExpired:client.kill();client.wait()
                client.stderr.close()
                process_event(root, {'hook_event_name': 'SessionEnd', 'session_id': 'host-session'})
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline and json.loads(state.read_text()).get('state') != 'Stopped':
                    time.sleep(.05)


if __name__ == '__main__':
    unittest.main()
