"""Installed aliases must resolve adjacent implementation and project context."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from aikya.installation.registration import setup
from aikya.installation.assets import runtime_assets

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / 'tests/fixtures/runtime-adapter-contracts.json').read_text())


class RuntimeAdapterContracts(unittest.TestCase):
    def test_installed_adapter_bytes_and_target_selections_remain_compatible(self):
        for kind, method in [('registration', None), ('initialized', 'odd'), ('initialized', 'sdd')]:
            with self.subTest(kind=kind, method=method):
                assets = runtime_assets(ROOT, kind, methodology=method)
                names = {name + '.py' for name in CONTRACT['adapters']} | {'_aikya_bootstrap.py'}
                selected = [a for a in assets if a.kind != 'package' and a.destination.parts[0] != 'compatibility' and a.destination.name in names]
                key = kind + ('-' + method if method else '')
                # Helpers move from template-copy ownership into runtime inventory.
                expected = set(CONTRACT['destinations'][key])
                if kind == 'initialized':
                    expected |= {name + '.py' for name, row in CONTRACT['adapters'].items() if row['helper']}
                actual = {a.destination.as_posix() for a in selected}
                self.assertEqual(expected, actual)
                for asset in selected:
                    raw = asset.read_bytes()
                    digest = hashlib.sha256(raw).hexdigest()
                    want = CONTRACT['bootstrap_sha256'] if asset.destination.name == '_aikya_bootstrap.py' else CONTRACT['adapters'][asset.destination.stem]['sha256']
                    self.assertEqual(want, digest, str(asset.destination))

    def test_registered_alias_uses_adjacent_package_from_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary); target = base / 'project'; target.mkdir()
            setup(ROOT, target, 'project', home=base / 'home')
            runtime = target / '.aikya/runtime'
            code = ('import sys;sys.path.insert(0,' + repr(str(runtime)) + ');'
                    'import aikya_session;from aikya.cli import session;assert aikya_session is session;'
                    'import docs_layout;from aikya.documentation import layout;assert docs_layout is layout;'
                    'assert ' + repr(str(runtime)) + ' in session.__file__')
            result = subprocess.run([sys.executable, '-B', '-c', code], cwd=base,
                                    env={**os.environ, 'PYTHONPATH': ''}, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse(list(runtime.rglob('__pycache__')))
