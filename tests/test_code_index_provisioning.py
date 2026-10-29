import unittest
from aikya.installation.bootstrap.options import parser
from aikya.installation.bootstrap.code_index import selection, requirements, PINS
from aikya.code_index.parsers.treesitter import PINS as PARSER_PINS

class ProvisionTests(unittest.TestCase):
    def test_selection_is_explicit_and_update_preserves(self):
        self.assertEqual(parser().parse_args(['install','--code-index','dart']).code_index,'dart')
        self.assertEqual(selection(None,{'code_index':'dart'},'update'),'dart')
        self.assertEqual(selection(None,{},'install'),'none')
        self.assertEqual(selection('none',{'code_index':'all'},'update'),'none')
    def test_pins_match_parsers_and_none_has_no_dependencies(self):
        self.assertEqual(PINS,PARSER_PINS)
        self.assertEqual(requirements('none'),[])
        self.assertEqual(len(requirements('dart')),2)
        with self.assertRaises(ValueError):requirements('anything')


class ParserIntegrityTests(unittest.TestCase):
    def test_missing_and_corrupt_assets_fail_before_provisioning(self):
        import hashlib
        import tempfile
        from pathlib import Path
        from aikya.installation.bootstrap.code_index import prepare
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();offline=root/'assets';offline.mkdir()
            core='tree_sitter-0.25.2-cp313-cp313-any.whl'
            dart='tree_sitter_dart-0.1.0-cp38-abi3-any.whl'
            (offline/'SHA256SUMS').write_text('0'*64+'  '+core+'\n'+'0'*64+'  '+dart+'\n')
            with self.assertRaises(ValueError):prepare('dart','7.2.0',root/'stage',offline)
            (offline/core).write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'integrity'):prepare('dart','7.2.0',root/'stage',offline)
            self.assertFalse((root/'stage').exists())

if __name__=='__main__':unittest.main()
