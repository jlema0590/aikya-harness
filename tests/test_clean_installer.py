"""Clean installation rejects corrupt assets before changing a user environment."""
import hashlib
import importlib
import io
import contextlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class CleanInstaller(unittest.TestCase):
    def core(self, name):
        try:
            return importlib.import_module('aikya.installation.bootstrap.' + name)
        except ModuleNotFoundError:
            self.fail('Clean cross-platform installer is not implemented')

    def test_offline_release_checks_hash_and_copies_only_matching_wheel(self):
        download = self.core('download')
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve(); source = base / 'release'; source.mkdir()
            name = 'aikya_harness-7.0.0-py3-none-any.whl'; wheel = source / name
            wheel.write_bytes(b'controlled-wheel')
            checksum = hashlib.sha256(wheel.read_bytes()).hexdigest()
            (source / 'SHA256SUMS').write_text(checksum + '  ' + name + '\n')
            assets = download.fetch_release('7.0.0', base / 'download', source)
            self.assertEqual(b'controlled-wheel', assets['wheel'].read_bytes())
            wheel.write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'checksum|integrity'):
                download.fetch_release('7.0.0', base / 'other', source)
            self.assertFalse((base / 'other' / name).exists())

    def test_manifest_rejects_traversal_duplicates_and_invalid_versions(self):
        download = self.core('download')
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            for payload in ('0' * 64 + '  ../outside.whl\n', ('0' * 64 + '  a.whl\n') * 2, 'invalid checksum\n'):
                (base / 'SHA256SUMS').write_text(payload)
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    download.fetch_release('7.0.0', base / 'target', base)
            for version in ('../main', 'main', '7.0.0;id', 'v7.0.0', '07.0.0'):
                with self.subTest(version=version), self.assertRaises(ValueError):
                    download.fetch_release(version, base / 'target', base)

    def test_dry_run_does_not_create_installation_or_project_files(self):
        cli = self.core('cli')
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve(); project = base / 'project'; project.mkdir()
            with patch.dict(os.environ, {'AIKYA_INSTALL_ROOT': str(base / 'app')}), contextlib.redirect_stdout(io.StringIO()):
                result = cli.main(['install', '--version', '7.0.0', '--scope', 'project', '--target', str(project), '--mods', 'none', '--dry-run'])
            self.assertEqual(0, result)
            self.assertFalse((base / 'app').exists())
            self.assertEqual([], list(project.iterdir()))

    def test_project_scope_requires_existing_explicit_target(self):
        cli = self.core('cli')
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            with patch.dict(os.environ, {'AIKYA_INSTALL_ROOT': str(base / 'app')}), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(2, cli.main(['install', '--version', '7.0.0', '--scope', 'project', '--dry-run']))
            self.assertFalse((base / 'app').exists())

    def test_empty_platform_storage_variable_falls_back_to_user_home(self):
        module = self.core('environment')
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            with patch.dict(os.environ, {'HOME': str(home), 'USERPROFILE': str(home), 'XDG_DATA_HOME': '', 'AIKYA_INSTALL_ROOT': ''}), patch('sys.platform', 'linux'):
                self.assertEqual(home / '.local/share/aikya', module.app_root())
