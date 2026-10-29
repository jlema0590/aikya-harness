import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from aikya.documentation import guard
from aikya.middleware.commands import recipe

class PreflightTests(unittest.TestCase):
    def test_preflight_and_stop_agree(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(guard,'ROOT',Path(folder)):
            state={'request_id':'REQ-20261029-12345678','kind':'general','baseline':{'src/a.py':'old'}}
            current={'src/a.py':'new'}
            value=guard.preflight_request(state,current)
            self.assertEqual(value['ready'],guard.validate_request(state,current)[0])
            self.assertIn('aikya/docs/overview.md',value['required'])
            self.assertIn('aikya/docs/changes/REQ-20261029-12345678.md',value['required'])
            self.assertFalse(list(Path(folder).iterdir()))
    def test_read_only_does_not_create_empty_dossier(self):
        state={'request_id':'x','kind':'feature','baseline':{}}
        self.assertEqual(guard.preflight_request(state,{})['required'],[])
    def test_inspect_does_not_require_implementation_or_security(self):
        for command in ('aikya-models','aikya-quality','aikya-tests','aikya-verify','aikya-sdd-status'):
            self.assertNotIn('implement',recipe(command,action='inspect')['required'])
            self.assertIn('security',recipe(command,action='write')['required'])

if __name__=='__main__':unittest.main()
