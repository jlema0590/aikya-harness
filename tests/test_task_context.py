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


class NaturalNameTests(unittest.TestCase):
    def test_words_match_camel_case_and_snake_case(self):
        from aikya.context.ranking import rank
        self.assertLess(rank({'name':'signIn','path':'user.dart'},'change sign in')[0],0)
        self.assertLess(rank({'name':'sign_in','path':'user.py'},'change sign in')[0],0)

class UnavailableIndexTests(unittest.TestCase):
    def test_copied_index_is_preserved_and_fallback_uses_only_current_project(self):
        import shutil
        from aikya.code_index.sync import sync
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            first=Path(a).resolve();second=Path(b).resolve()
            configure(first,approved=True);configure(second,approved=True)
            (first/'x.py').write_text('class First: pass');(second/'x.py').write_text('class Second: pass')
            sync(first,full=True);shutil.copytree(first/'.harness',second/'.harness')
            database=second/'.harness/state/code-index/index.sqlite';before=database.read_bytes()
            packet=prepare_context(second,'Second',paths=['x.py'])
            self.assertIn('index_unavailable',packet['diagnostics'])
            self.assertIn('Second',json.dumps(packet));self.assertNotIn('First',json.dumps(packet))
            self.assertEqual(database.read_bytes(),before)

if __name__=='__main__':unittest.main()
