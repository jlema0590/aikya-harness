import runtime_support
"""Interrupted managed copies and stale previews must preserve previous bytes."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aikya.installation import registration as aikya_setup
from aikya.installation import runtime as bundle


class RuntimeTransactionTests(unittest.TestCase):
    def prepare_old_owned_files(self, base):
        target = base / 'project'
        aikya_setup.setup(ROOT, target, 'project', home=base / 'home')
        runtime = target / '.aikya/runtime'
        originals = {}
        manifest_file = runtime / '.bundle-manifest.json'
        manifest = json.loads(manifest_file.read_text())
        for name in ('aikya_cli.py', 'src/aikya/documentation/layout.py'):
            raw = b'# Controlled managed predecessor\n'
            (runtime / name).write_bytes(raw)
            originals[name] = raw
            manifest['files'][name] = hashlib.sha256(raw).hexdigest()
        manifest_file.write_text(json.dumps(manifest))
        return runtime, originals

    def test_copy_failure_restores_previous_files_and_retry_succeeds(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime, originals = self.prepare_old_owned_files(Path(temporary))
            operations = bundle.prepare_bundle(runtime, ROOT, 'registration')
            manifest = (runtime / '.bundle-manifest.json').read_bytes()
            real_write = bundle.atomic_write

            def fail_launcher(path, data):
                if Path(path) == runtime / 'aikya_cli.py' and data != originals['aikya_cli.py']:
                    raise OSError('Controlled adapter copy failure')
                return real_write(path, data)

            with patch.object(bundle, 'atomic_write', side_effect=fail_launcher):
                with self.assertRaises(OSError):
                    bundle.apply_bundle(runtime, operations, [])
            for name, raw in originals.items():
                self.assertEqual(raw, (runtime / name).read_bytes())
            self.assertEqual(manifest, (runtime / '.bundle-manifest.json').read_bytes())
            bundle.apply_bundle(runtime, bundle.prepare_bundle(runtime, ROOT, 'registration'), [])
            self.assertEqual(runtime_support.generated_bytes('aikya_cli.py'), (runtime / 'aikya_cli.py').read_bytes())

    def test_stale_preview_rejects_owner_edit_before_other_files_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime, originals = self.prepare_old_owned_files(Path(temporary))
            operations = bundle.prepare_bundle(runtime, ROOT, 'registration')
            path = runtime / 'aikya_cli.py'
            path.write_bytes(b'# Owner edit after preflight\n')
            with self.assertRaisesRegex(ValueError, 'changed after'):
                bundle.apply_bundle(runtime, operations, [])
            self.assertEqual(b'# Owner edit after preflight\n', path.read_bytes())
            self.assertEqual(originals['src/aikya/documentation/layout.py'], (runtime / 'src/aikya/documentation/layout.py').read_bytes())
