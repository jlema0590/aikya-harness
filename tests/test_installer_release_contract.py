"""Published bootstrap runs without importing an installed Aikya package."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerReleaseContract(unittest.TestCase):
    def test_generated_zipapp_is_standalone_and_manifest_covers_scripts(self):
        builder = ROOT / 'scripts/ci/build_installers.py'
        self.assertTrue(builder.is_file(), 'Version-pinned installer artifact builder is missing')
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve(); out = base / 'assets'
            process = subprocess.run([sys.executable, str(builder), '--version', '7.0.0', '--output', str(out)], capture_output=True, text=True)
            self.assertEqual(0, process.returncode, process.stderr)
            digests = {line.split('  ')[1]: line.split('  ')[0] for line in (out / 'SHA256SUMS').read_text().splitlines()}
            for name in ('aikya-bootstrap.pyz', 'install.sh', 'install.ps1'):
                self.assertEqual(digests[name], hashlib.sha256((out / name).read_bytes()).hexdigest())
            env = {**os.environ, 'AIKYA_INSTALL_ROOT': str(base / 'app'), 'PYTHONPATH': '', 'HOME': str(base / 'home'), 'USERPROFILE': str(base / 'home')}
            process = subprocess.run([sys.executable, '-I', '-B', str(out / 'aikya-bootstrap.pyz'), 'install', '--version', '7.0.0', '--scope', 'global', '--mods', 'none', '--dry-run'], cwd=base, env=env, capture_output=True, text=True)
            self.assertEqual(0, process.returncode, process.stderr)
            self.assertFalse((base / 'app').exists())
            first = (out / 'aikya-bootstrap.pyz').read_bytes()
            subprocess.run([sys.executable, str(builder), '--version', '7.0.0', '--output', str(out)], check=True, capture_output=True)
            self.assertEqual(first, (out / 'aikya-bootstrap.pyz').read_bytes())

    def test_release_rejects_wrong_wheel_metadata_and_conflicting_published_assets(self):
        from scripts.ci.release_assets import verify_assets, compare_assets
        import zipfile
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary); wheel = base / 'aikya_harness-7.0.0-py3-none-any.whl'
            names = ['aikya_harness-7.0.0.tar.gz', 'aikya-harness-v7.0.0.zip', 'aikya-bootstrap.pyz', 'install.sh', 'install.ps1']
            for name in names:
                (base / name).write_bytes(b'controlled-payload')
            def metadata(version):
                with zipfile.ZipFile(wheel, 'w') as archive:
                    archive.writestr('aikya_harness-7.0.0.dist-info/METADATA', 'Name: aikya-harness\nVersion: ' + version + '\n')
                    archive.writestr('aikya_harness-7.0.0.dist-info/WHEEL', 'Wheel-Version: 1.0\nTag: py3-none-any\n')
                (base / 'SHA256SUMS').write_text(''.join(hashlib.sha256((base / name).read_bytes()).hexdigest() + '  ' + name + '\n' for name in [wheel.name, *names]))
            metadata('0.0.1')
            with self.assertRaisesRegex(ValueError, 'metadata|version'):
                verify_assets(base, '7.0.0')
            metadata('7.0.0')
            self.assertEqual(7, len(verify_assets(base, '7.0.0')))
            existing = base / 'published'; existing.mkdir()
            (existing / 'install.sh').write_bytes(b'conflicting-published-script')
            with self.assertRaisesRegex(ValueError, 'conflict|overwrite'):
                compare_assets(base, existing, '7.0.0')
            (existing / 'install.sh').write_bytes((base / 'install.sh').read_bytes())
            self.assertNotIn('install.sh', compare_assets(base, existing, '7.0.0'))
