"""Generated inputs must retain ownership, preflight and rollback protections."""
import importlib
from pathlib import Path
import shutil
import tempfile
import unittest
from aikya.installation.assets import AssetRecord
from aikya.installation.runtime import prepare_bundle, apply_bundle

ROOT = Path(__file__).resolve().parents[1]


class GeneratedAssetTransactions(unittest.TestCase):
    def test_generated_asset_reads_and_digests_live_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'input'; path.write_bytes(b'one')
            try:
                asset = AssetRecord(None, Path('example.py'), 'adapter', producer=lambda: b'payload', inputs=(path,))
            except TypeError:
                self.fail('AssetRecord cannot represent a generated source')
            self.assertEqual(b'payload', asset.read_bytes())
            first = asset.source_digest()
            path.write_bytes(b'two')
            self.assertNotEqual(first, asset.source_digest())
            path.unlink(); path.symlink_to(ROOT / 'VERSION')
            with self.assertRaises(ValueError):
                asset.read_bytes()

    def test_generated_mapping_drift_rejects_before_any_target_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary); source = base / 'source'; runtime = base / 'runtime'
            shutil.copytree(ROOT / 'src', source / 'src', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            for name in ('requirements-agent-loop.txt', 'VERSION'):
                shutil.copy2(ROOT / name, source / name)
            shutil.copytree(ROOT / 'docs', source / 'docs')
            try:
                operations = prepare_bundle(runtime, source, 'registration')
            except (FileNotFoundError, ValueError):
                self.fail('Runtime preflight still requires checked-in root launchers')
            mapping = source / 'src/aikya/module_map.json'
            mapping.write_text(mapping.read_text() + '\n')
            with self.assertRaisesRegex(ValueError, 'preflight|changed'):
                apply_bundle(runtime, operations, [])
            self.assertFalse(runtime.exists())

    def test_file_and_generated_sources_are_mutually_exclusive(self):
        with self.assertRaises((ValueError, TypeError)):
            AssetRecord(ROOT / 'VERSION', Path('bad'), 'adapter', producer=lambda: b'bad')
