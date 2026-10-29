import json
from pathlib import Path
import tempfile
import unittest
from aikya.context.prepare import prepare_context
from aikya.code_index.policy import configure

class TaskContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
        (self.root/'login.py').write_text('class Login:\n    def sign_in(self):\n        return "fresh"\n')
        (self.root/'other.py').write_text('class Other: pass\n')
    def test_sentence_ranking_and_packet_budget_without_duplication(self):
        configure(self.root,approved=True)
        value=prepare_context(self.root,'please change the sign_in method',paths=['login.py'],max_chars=1200)
        self.assertLessEqual(len(json.dumps(value,ensure_ascii=False)),1200)
        self.assertIn('sign_in',json.dumps(value))
        self.assertNotIn('other.py',json.dumps(value))
        self.assertLessEqual(json.dumps(value).count('return'),1)
    def test_missing_index_fallback_and_no_scope_widening(self):
        value=prepare_context(self.root,'change sign_in',paths=['login.py'])
        self.assertIn('index_disabled',value['diagnostics']);self.assertTrue(value['context'])
        self.assertFalse(prepare_context(self.root,'sign_in',paths=[])['context'])
    def test_external_change_and_exclusions_are_current(self):
        configure(self.root,approved=True)
        prepare_context(self.root,'Login',paths=['login.py'])
        (self.root/'login.py').write_text('class Replacement: pass\n')
        value=prepare_context(self.root,'Replacement',paths=['login.py'])
        self.assertNotIn('fresh',json.dumps(value));self.assertIn('Replacement',json.dumps(value))
        with self.assertRaises(ValueError):prepare_context(self.root,'x',paths=['../outside.py'])

if __name__=='__main__':unittest.main()
