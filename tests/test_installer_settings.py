"""Ownership receipts record generated settings deltas, never user credentials."""
import base64
import importlib
import json
from pathlib import Path
import tempfile
import unittest


class InstallerSettings(unittest.TestCase):
    def module(self):
        try:
            return importlib.import_module('aikya.installation.bootstrap.settings')
        except ModuleNotFoundError:
            self.fail('Credential-free settings ownership is missing')

    def test_ownership_excludes_credentials_and_removes_only_generated_hooks(self):
        settings = self.module()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / 'settings.json'
            custom = {'env': {'ANTHROPIC_AUTH_TOKEN': 'synthetic-private-value'}, 'custom': True}
            added = {'hooks': [{'type': 'command', 'command': 'python /runtime/aikya_session.py'}]}
            installed = {**custom, 'hooks': {'SessionStart': [added]}}
            encode = lambda value: base64.b64encode(json.dumps(value).encode()).decode()
            before = {str(path): encode(custom)}; after = {str(path): encode(installed)}
            changes = settings.changes(before, after)
            self.assertNotIn('synthetic-private-value', json.dumps(changes))
            installed['user_added_after_install'] = 42
            path.write_text(json.dumps(installed))
            settings.remove(changes, Path('/runtime'))
            self.assertEqual({**custom, 'user_added_after_install': 42}, json.loads(path.read_text()))

    def test_edited_owned_hook_is_preserved_before_runtime_removal(self):
        settings = self.module()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / 'settings.json'
            original = {'hooks': {'SessionStart': [{'hooks': [{'type': 'command', 'command': 'python /runtime/aikya_session.py'}]}]}}
            encode = lambda value: base64.b64encode(json.dumps(value).encode()).decode()
            changes = settings.changes({}, {str(path): encode(original)})
            changed = json.loads(json.dumps(original)); changed['hooks']['SessionStart'][0]['hooks'][0]['command'] += ' --custom'
            path.write_text(json.dumps(changed)); before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, 'edited|Edited'):
                settings.remove(changes, Path('/runtime'))
            self.assertEqual(before, path.read_bytes())
