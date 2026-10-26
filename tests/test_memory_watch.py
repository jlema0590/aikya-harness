"""Real local changes propagate without providers, approval mutation or self loops."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest


class MemoryWatchTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.memory.viewer.watch'), 'Automatic local updating is missing')
        from aikya.code_index.policy import configure
        from aikya.memory.viewer.watch import watch_project
        from aikya.memory.viewer.contracts import WatchOptions
        self.watch, self.Options = watch_project, WatchOptions
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve();configure(self.root, approved=True)
        self.source = self.root / 'orders.py';self.source.write_text('class Before: pass\n')
        self.stop = threading.Event();self.errors = []
        self.thread = None
        self.addCleanup(self.close)

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(5)
            self.assertFalse(self.thread.is_alive(), 'Watcher did not stop')

    def start(self):
        def run():
            try:
                self.watch(self.root, options=self.Options(poll_interval_ms=50, debounce_ms=0, reconcile_interval_s=1), stop_event=self.stop)
            except Exception as error:
                self.errors.append(error)
        self.thread = threading.Thread(target=run)
        self.thread.start()
        self.wait(lambda: self.html().exists())

    def html(self):
        return self.root / 'aikya/docs/memory/view/index.html'

    def wait(self, check):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if self.errors:
                raise self.errors[0]
            try:
                if check():
                    return
            except (FileNotFoundError, PermissionError):
                # Windows can deny a read during atomic replacement. Retry only
                # within the same deadline; observer errors still fail above.
                pass
            time.sleep(.025)
        self.fail('Local update did not converge within the test timeout')

    def test_external_create_edit_rename_and_delete_update_html(self):
        self.start()
        new = self.root / 'external.py';new.write_text('class Created: pass\n')
        self.wait(lambda: 'Created' in self.html().read_text())
        replacement = self.root / 'temporary.py';replacement.write_text('class Updated: pass\n')
        os.replace(replacement, new)
        self.wait(lambda: 'Updated' in self.html().read_text() and 'Created' not in self.html().read_text())
        new.rename(self.root / 'renamed.py')
        self.wait(lambda: 'renamed.py' in self.html().read_text() and 'external.py' not in self.html().read_text())
        (self.root / 'renamed.py').unlink()
        self.wait(lambda: 'Updated' not in self.html().read_text())

    def test_unchanged_cycles_do_not_rewrite_export_or_create_watch_loops(self):
        self.start()
        report = self.root / 'aikya/docs/memory/view/report.md'
        self.wait(report.exists)
        before = self.html().stat().st_mtime_ns
        time.sleep(1.3)
        self.assertEqual(before, self.html().stat().st_mtime_ns)
        self.assertFalse(self.errors)

    def test_periodic_reconciliation_finds_same_metadata_changes(self):
        self.start()
        previous = self.source.stat()
        self.source.write_text('class After_: pass\n')
        os.utime(self.source, ns=(previous.st_atime_ns, previous.st_mtime_ns))
        self.wait(lambda: 'After_' in self.html().read_text())

    def test_user_cannot_start_two_watchers_for_one_worktree(self):
        self.start()
        with self.assertRaises(ValueError):
            self.watch(self.root, options=self.Options(), stop_event=threading.Event())

    def test_restart_reconciles_changes_made_while_stopped(self):
        self.start();self.close()
        self.source.write_text('class WhileStopped: pass\n')
        self.stop = threading.Event();self.errors = [];self.start()
        self.wait(lambda: 'WhileStopped' in self.html().read_text())

    def test_disabling_policy_stops_watcher_without_enabling_index(self):
        self.start()
        path = self.root / '.aikya/code-index.json'
        policy = json.loads(path.read_text());policy['watch'] = False
        path.write_text(json.dumps(policy))
        self.thread.join(5)
        self.assertFalse(self.thread.is_alive())
        self.assertFalse(json.loads(path.read_text())['watch'])

    def test_note_expiry_updates_view_without_touching_any_source_file(self):
        from aikya.memory.knowledge import remember
        from aikya.memory.viewer.publication import read_publication
        note = remember(self.root, {'kind': 'reference', 'text': 'Temporary rule', 'source': 'orders.py', 'ttl_days': 1},
                        approved=True, now=time.time() - 86400 + 2)
        before = (self.root / note).read_bytes()
        self.start()
        def expired():
            try:
                snapshot, _ = read_publication(self.root)
                return any(n['type'] == 'memory' and n['details']['expired'] for n in snapshot.nodes)
            except (OSError, ValueError):
                return False
        self.wait(expired)
        self.assertEqual(before, (self.root / note).read_bytes())


if __name__ == '__main__':
    unittest.main()
