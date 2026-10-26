"""Rendering must preserve installed behavior and reject executable mapping data."""
import hashlib
import importlib
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GeneratedAdapters(unittest.TestCase):
    def renderer(self):
        try:
            return importlib.import_module('aikya.installation.compatibility')
        except ModuleNotFoundError:
            self.fail('The validated runtime adapter renderer is not implemented')

    def test_all_rendered_adapters_match_frozen_installed_bytes(self):
        renderer = self.renderer()
        mapping = renderer.load_module_map(ROOT / 'src/aikya/module_map.json')
        template = (ROOT / 'src/aikya/resources/compatibility/adapter.py.tmpl').read_bytes()
        fixture = json.loads((ROOT / 'tests/fixtures/runtime-adapter-contracts.json').read_text())
        for name, contract in fixture['adapters'].items():
            with self.subTest(name=name):
                raw = renderer.render_adapter(name, mapping, template)
                self.assertEqual(contract['sha256'], hashlib.sha256(raw).hexdigest())
        with self.assertRaises(ValueError):
            renderer.render_adapter('unknown', mapping, template)
        with self.assertRaises(ValueError):
            renderer.render_adapter('install', mapping, b'not a launcher')

    def test_mapping_rejects_duplicate_keys_paths_and_foreign_modules(self):
        renderer = self.renderer()
        for payload in ('{"install":"installation.facade","install":"cli.main"}',
                        '{"../install":"installation.facade"}', '{"install":"os.system"}',
                        '{"install":"installation.facade;print(1)"}', '[]'):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / 'module_map.json'; path.write_text(payload)
                with self.assertRaises(ValueError):
                    renderer.load_module_map(path)
