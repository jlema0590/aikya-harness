"""Local indexing must never return obsolete symbols or escape project scope."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class CodeIndexTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.code_index'), 'Local code index is missing')
        from aikya.code_index.policy import configure
        from aikya.code_index.sync import sync
        from aikya.code_index.store import IndexStore
        from aikya.code_index.query import query
        self.configure, self.sync, self.Store, self.query = configure, sync, IndexStore, query
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.configure(self.root, approved=True)

    def source(self, name='service.py', text='class UserService:\n    def create(self, name: str):\n        return name\n'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf8')
        return path

    def test_changed_file_replaces_symbols_and_unchanged_files_are_not_parsed(self):
        path = self.source()
        self.source('second.py', 'def other():\n    return 2\n')
        first = self.sync(self.root)
        self.assertEqual(2, first.parsed_files)
        unchanged = self.sync(self.root)
        self.assertEqual(0, unchanged.parsed_files)
        self.assertEqual(first.generation, unchanged.generation)
        path.write_text('class Account:\n    pass\n')
        changed = self.sync(self.root)
        self.assertEqual(1, changed.parsed_files)
        self.assertGreater(changed.generation, first.generation)
        self.assertEqual([], self.query(self.root, 'UserService').matches)
        self.assertEqual('Account', self.query(self.root, 'Account').matches[0]['name'])

    def test_deleted_renamed_and_syntax_error_sources_do_not_keep_current_symbols(self):
        path = self.source()
        self.sync(self.root)
        path.rename(self.root / 'renamed.py')
        self.sync(self.root)
        self.assertEqual('renamed.py', self.query(self.root, 'UserService').matches[0]['path'])
        (self.root / 'renamed.py').write_text('class Broken(\n')
        result = self.sync(self.root)
        self.assertEqual('partial', result.status)
        self.assertEqual([], self.query(self.root, 'UserService').matches)
        (self.root / 'renamed.py').unlink()
        self.sync(self.root)
        self.assertEqual([], self.Store(self.root).read_snapshot().files)

    def test_same_size_and_timestamp_content_changes_are_reconciled(self):
        path = self.source(text='class Before: pass\n')
        self.sync(self.root)
        stamp = path.stat()
        path.write_text('class After_: pass\n')
        os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        self.sync(self.root, full=True)
        self.assertEqual([], self.query(self.root, 'Before').matches)
        self.assertEqual('After_', self.query(self.root, 'After_').matches[0]['name'])

    def test_queries_revalidate_content_and_obey_allowed_files_and_context_budget(self):
        path = self.source()
        self.source('other/service.py')
        self.sync(self.root)
        result = self.query(self.root, 'UserService', allowed_files=['service.py'], max_chars=160)
        self.assertEqual({'service.py'}, {m['path'] for m in result.matches})
        self.assertLessEqual(len(result.context), 160)
        path.write_text('class Replacement: pass\n')
        self.assertEqual([], self.query(self.root, 'UserService', allowed_files=['service.py']).matches)
        self.assertEqual([], self.query(self.root, 'UserService', allowed_files=[]).matches)
        with self.assertRaises(ValueError):
            self.query(self.root, 'UserService', allowed_files=['../outside.py'])

    def test_non_python_is_honestly_inventory_only(self):
        self.source('User.kt', 'class User { void save() {} }\n')
        self.sync(self.root)
        entry = self.Store(self.root).read_snapshot().files[0]
        self.assertEqual('file_only', entry['status'])
        result = self.query(self.root, 'User.kt')
        self.assertEqual('file', result.matches[0]['kind'])

    def test_utf8_positions_nested_names_and_imports_are_source_bound(self):
        text = 'import os\nclass Café:\n    def run(self):\n        return "á"\n'
        for newline in ('\n', '\r\n'):
            with self.subTest(newline=repr(newline)):
                raw = text.replace('\n', newline).encode('utf8')
                (self.root / 'service.py').write_bytes(raw)
                self.sync(self.root)
                snap = self.Store(self.root).read_snapshot()
                method = next(s for s in snap.symbols if s['qualified_name'] == 'Café.run')
                self.assertEqual('run', method['name'])
                self.assertEqual(3, method['start_line'])
                self.assertTrue(raw[method['start_byte']:method['end_byte']].startswith(b'def run'))
                self.assertEqual('os', snap.imports[0]['name'])

    def test_secret_and_symlink_paths_are_excluded_without_execution(self):
        self.source()
        self.source('secrets/leak.py', 'raise RuntimeError("must not execute")\n')
        self.source('.env.py', 'class Password: pass\n')
        self.source('node_modules/vendor.py')
        self.source('nested/.git', 'gitdir: elsewhere\n')
        self.source('nested/submodule.py')
        if hasattr(os, 'symlink'):
            (self.root / 'link.py').symlink_to(self.root / 'service.py')
        self.sync(self.root)
        self.assertEqual(['service.py'], [f['path'] for f in self.Store(self.root).read_snapshot().files])

    @unittest.skipUnless(shutil.which('git'), 'Git required for ignore semantics')
    def test_git_ignored_files_and_directories_are_not_read(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / '.gitignore').write_text('ignored/\n*.private.py\n')
        self.source('ignored/a.py')
        self.source('hidden.private.py')
        self.source()
        self.sync(self.root)
        self.assertEqual(['service.py'], [f['path'] for f in self.Store(self.root).read_snapshot().files])

    def test_disabled_or_missing_policy_never_creates_cache(self):
        self.source()
        policy = self.root / '.aikya/code-index.json'
        value = json.loads(policy.read_text())
        value['enabled'] = False
        policy.write_text(json.dumps(value))
        result = self.sync(self.root)
        self.assertEqual('disabled', result.status)
        self.assertFalse((self.root / '.harness').exists())
        policy.unlink()
        self.assertEqual('disabled', self.sync(self.root).status)
        self.assertFalse(policy.exists())

    def test_policy_requires_authorization_and_preserves_custom_files(self):
        with self.assertRaises(ValueError):
            self.configure(self.root)
        policy = self.root / '.aikya/code-index.json'
        policy.write_text('{"team": "custom"}\n')
        with self.assertRaises(ValueError):
            self.configure(self.root, approved=True)
        self.assertEqual('{"team": "custom"}\n', policy.read_text())

    def test_cache_copied_to_another_project_is_never_trusted(self):
        self.source()
        self.sync(self.root)
        with tempfile.TemporaryDirectory() as other:
            target = Path(other).resolve()
            shutil.copytree(self.root / '.harness', target / '.harness')
            shutil.copytree(self.root / '.aikya', target / '.aikya')
            with self.assertRaises(ValueError):
                self.Store(target).read_snapshot()

    def test_limits_report_partial_and_reject_oversized_reads(self):
        self.source('large.py', 'a' * (1024 * 1024 + 1))
        self.source()
        result = self.sync(self.root)
        self.assertEqual('partial', result.status)
        self.assertEqual('oversized', self.Store(self.root).read_snapshot().files[0]['status'])
        self.assertEqual([], self.query(self.root, 'large.py').matches)

    def test_component_policy_does_not_index_unapproved_siblings(self):
        self.source('allowed/service.py')
        self.source('outside/private.py')
        policy = self.root / '.aikya/code-index.json'
        value = json.loads(policy.read_text());value['scope'] = 'allowed'
        policy.write_text(json.dumps(value))
        self.sync(self.root)
        self.assertEqual(['allowed/service.py'], [f['path'] for f in self.Store(self.root).read_snapshot().files])

    def test_clear_rejects_unowned_cache_and_preserves_policy(self):
        from aikya.code_index.__main__ import main
        self.source();self.sync(self.root)
        self.assertEqual(2, main(['clear', '--root', str(self.root)]))
        path = self.root / '.harness/state/code-index/index.sqlite'
        path.write_text('Team database')
        self.assertEqual(2, main(['clear', '--root', str(self.root), '--approved']))
        self.assertEqual('Team database', path.read_text())

    def test_failed_transaction_preserves_the_previous_generation(self):
        self.source();self.sync(self.root)
        before = self.Store(self.root).read_snapshot()
        with self.assertRaises(RuntimeError):
            with self.Store(self.root).connect(write=True) as connection:
                connection.execute('DELETE FROM symbols')
                raise RuntimeError('Interrupted write')
        after = self.Store(self.root).read_snapshot()
        self.assertEqual(before.symbols, after.symbols)
        self.assertEqual(before.generation, after.generation)

    def test_unchanged_oversized_files_do_not_create_new_generations(self):
        self.source('large.py', 'x' * (1048576 + 1))
        first = self.sync(self.root)
        second = self.sync(self.root)
        self.assertEqual(first.generation, second.generation)
        self.assertEqual('partial', second.status)

    def test_byte_limited_batches_eventually_index_later_files(self):
        policy = self.root / '.aikya/code-index.json'
        value = json.loads(policy.read_text());value['max_sync_bytes'] = 35
        policy.write_text(json.dumps(value))
        for name in ('Alpha', 'Bravo', 'Charlie'):
            self.source(name + '.py', 'class ' + name + ': pass\n')
        for _ in range(4):
            self.sync(self.root)
        snapshot = self.Store(self.root).read_snapshot()
        self.assertEqual({'Alpha', 'Bravo', 'Charlie'}, {s['name'] for s in snapshot.symbols})
        self.assertEqual('partial', snapshot.status)


if __name__ == '__main__':
    unittest.main()
