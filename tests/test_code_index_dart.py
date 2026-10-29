import unittest
import importlib.util
from aikya.code_index.parsers import registry
from aikya.code_index.coverage import summarize

SOURCE="""import 'dart:io';
class Login { Login.named(); void signIn(String user) {print(user);} }
String greet() => 'héllo';
mixin Track {void log() {}}
extension Label on String {String title() => this;}
enum Role {admin, user}
""".encode()

class DartTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('tree_sitter_dart'), 'Optional Dart binary is not installed')
    def test_declarations_ranges_and_imports(self):
        result=registry.parse_file('lib/login.dart',SOURCE)
        self.assertEqual(result.status,'indexed',result.diagnostics)
        names={s['qualified_name']:s for s in result.symbols}
        self.assertTrue({'Login','Login.named','Login.signIn','greet','Track','Track.log','Label','Label.title','Role'}<=names.keys(),names.keys())
        self.assertIn(b'{print(user);}',SOURCE[names['Login.signIn']['start_byte']:names['Login.signIn']['end_byte']])
        self.assertEqual(len(result.imports),1)
        self.assertEqual(registry.parse_file('a.dart',SOURCE.replace(b'\n',b'\r\n')).status,'indexed')
    @unittest.skipUnless(importlib.util.find_spec('tree_sitter_dart'), 'Optional Dart binary is not installed')
    def test_invalid_syntax_does_not_publish_symbols(self):
        result=registry.parse_file('a.dart',b'class Broken { void f(')
        self.assertEqual(result.status,'parse_error');self.assertFalse(result.symbols)
    def test_coverage_distinguishes_file_only_and_indexed(self):
        value=summarize([{'path':'a.dart','status':'indexed'},{'path':'a.swift','status':'file_only'}],[])
        self.assertEqual(value['.dart']['indexed'],1);self.assertEqual(value['.swift']['file_only'],1)

if __name__=='__main__':unittest.main()
