"""Renamed catalogs must work and retire only unchanged predecessor assets."""
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
from aikya.resource_paths import source_path
from aikya.documentation import templates as templates


class TemplatePathUpgradeTests(unittest.TestCase):
    def legacy_runtime(self, base):
        project = base / 'project'
        aikya_setup.setup(ROOT, project, 'project', home=base / 'home')
        runtime = project / '.aikya/runtime'
        current = runtime / 'aikya-template'
        if current.exists():
            (current / 'docs').rename(current / 'milkeles')
            current.rename(runtime / 'documentation-templates')
        manifest = runtime / '.bundle-manifest.json'
        data = json.loads(manifest.read_text())
        data['files'] = {key.replace('aikya-template/docs/', 'documentation-templates/milkeles/').replace('aikya-template/', 'documentation-templates/'): value for key, value in data['files'].items()}
        manifest.write_text(json.dumps(data))
        return runtime

    def test_new_catalog_and_generated_references_use_aikya_paths(self):
        library = source_path(ROOT, 'aikya-template')
        self.assertTrue((library / 'docs/LICENSE').is_file())
        self.assertEqual(library, templates.LIBRARY)
        self.assertEqual(120, templates.validate_catalog()['templates'])
        for record in templates.catalog().values():
            self.assertTrue(record['path'].startswith('docs/'))
            self.assertEqual('aikya', record['provider'])
            self.assertNotIn('milkeles', record['source'].lower())

    def test_unchanged_legacy_catalog_is_backed_up_and_retired(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = self.legacy_runtime(Path(temporary))
            old = runtime / 'documentation-templates/milkeles/LICENSE'
            raw = old.read_bytes()
            operations = bundle.prepare_bundle(runtime, ROOT, 'registration')
            bundle.apply_bundle(runtime, operations, [])
            self.assertTrue((runtime / 'aikya-template/docs/LICENSE').is_file())
            self.assertFalse((runtime / 'documentation-templates').exists())
            backup = runtime / 'package-backups' / hashlib.sha256(raw).hexdigest() / 'documentation-templates/milkeles/LICENSE'
            self.assertEqual(raw, backup.read_bytes())
            self.assertNotIn('documentation-templates/milkeles/LICENSE', json.loads((runtime / '.bundle-manifest.json').read_text())['files'])

    def test_custom_legacy_catalog_blocks_before_writing_new_assets(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = self.legacy_runtime(Path(temporary))
            old = runtime / 'documentation-templates/milkeles/README.md'
            old.write_text(old.read_text() + '\nOwner customization.\n')
            before = {p.relative_to(runtime): p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
            with self.assertRaisesRegex(ValueError, 'Customized|customized'):
                bundle.prepare_bundle(runtime, ROOT, 'registration')
            self.assertEqual(before, {p.relative_to(runtime): p.read_bytes() for p in runtime.rglob('*') if p.is_file()})

    def test_retirement_rolls_back_when_manifest_write_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = self.legacy_runtime(Path(temporary))
            old = runtime / 'documentation-templates/milkeles/LICENSE'
            raw = old.read_bytes()
            before = (runtime / '.bundle-manifest.json').read_bytes()
            operations = bundle.prepare_bundle(runtime, ROOT, 'registration')
            real_write = bundle.atomic_write
            def fail_manifest(path, data):
                if Path(path) == runtime / '.bundle-manifest.json':
                    raise OSError('Controlled ownership write failure')
                return real_write(path, data)
            with patch.object(bundle, 'atomic_write', side_effect=fail_manifest):
                with self.assertRaises(OSError):
                    bundle.apply_bundle(runtime, operations, [])
            self.assertEqual(raw, old.read_bytes())
            self.assertFalse((runtime / 'aikya-template/docs/LICENSE').exists())
            self.assertEqual(before, (runtime / '.bundle-manifest.json').read_bytes())
