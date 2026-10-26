"""Activation and removal preserve active versions, edited assets and lock ownership."""
import importlib
import json
from pathlib import Path
import tempfile
import unittest


class InstallerRecovery(unittest.TestCase):
    def state(self):
        try:
            return importlib.import_module('aikya.installation.bootstrap.state')
        except ModuleNotFoundError:
            self.fail('Recoverable clean installer state is not implemented')

    def test_installation_lock_rejects_concurrent_mutation(self):
        state = self.state()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / 'app'
            with state.installation_lock(root):
                with self.assertRaisesRegex(ValueError, 'lock|progress'):
                    with state.installation_lock(root):
                        self.fail('Concurrent install acquired the same root')
            self.assertFalse((root / '.install.lock').exists())

    def test_restore_removes_owned_new_files_but_preserves_later_edits(self):
        state = self.state()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            one = root / 'one'; two = root / 'two'
            one.write_bytes(b'original')
            before = state.snapshot([root])
            one.write_bytes(b'installed'); two.write_bytes(b'new')
            after = state.snapshot([root])
            two.write_bytes(b'user edit')
            preserved = state.restore(before, after)
            self.assertEqual(b'original', one.read_bytes())
            self.assertEqual(b'user edit', two.read_bytes())
            self.assertIn(str(two), preserved)

    def test_unowned_or_symlinked_application_directory_is_rejected(self):
        state = self.state()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve(); root = base / 'app'; root.mkdir()
            (root / 'user.txt').write_text('user')
            with self.assertRaises(ValueError):
                with state.installation_lock(root):
                    pass
            link = base / 'linked'; link.symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                with state.installation_lock(link):
                    pass
            self.assertEqual('user', (root / 'user.txt').read_text())

    def test_initialized_projects_register_their_managed_interpreter_reference(self):
        state = self.state()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / 'app'
            with state.installation_lock(root):
                pass
            environment = root / 'versions/7.0.0/controlled'; environment.mkdir(parents=True)
            project = root.parent / 'project'; (project / '.harness').mkdir(parents=True)
            (project / '.harness/project-profile.json').write_text('{}')
            self.assertTrue(hasattr(state, 'record_project_reference'), 'Initialized projects cannot protect their managed interpreter')
            state.record_project_reference(project, environment)
            references = state.active_references(root)
            self.assertEqual(str(environment), references[0]['environment'])
            self.assertEqual(str(project), references[0]['target'])
