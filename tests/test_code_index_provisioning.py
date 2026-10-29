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

if __name__=='__main__':unittest.main()
