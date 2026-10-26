"""Worker effects and bounded protocol must work without selectable OS pipes."""
from pathlib import Path
import selectors
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from agent_loop_support import project, runtime


class RuntimeTransportTests(unittest.TestCase):
    def test_worker_completes_effect_acknowledgment_without_pipe_selectors(self):
        children, events = [], []
        launch = subprocess.Popen

        def tracked_launch(*args, **kwargs):
            process = launch(*args, **kwargs)
            children.append(process)
            return process

        with tempfile.TemporaryDirectory() as folder:
            root = project(folder)
            request = {'root': str(root), 'files': ['src/value.py'],
                       'phase': 'implement', 'timeout_seconds': 5}
            try:
                with patch('subprocess.Popen', side_effect=tracked_launch), patch.object(
                        selectors, 'DefaultSelector', side_effect=OSError('Pipe selection unavailable')):
                    result = runtime().execute(request, events.append)
                self.assertEqual('done', result['output']['status'])
                self.assertEqual('VALUE = 1\n', (root / 'src/value.py').read_text(encoding='utf8'))
                self.assertEqual(['effect_intent', 'effect_result'], [event['type'] for event in events])
                self.assertEqual(events[0]['id'], events[1]['id'])
            finally:
                for process in children:
                    if process.poll() is None:
                        process.kill()
                    process.wait(5)
                    process.stdin.close()
                    process.stdout.close()


if __name__ == '__main__':
    unittest.main()
