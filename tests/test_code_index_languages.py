"""Optional pinned grammars extract declarations, never runtime call targets."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class LanguageIndexTests(unittest.TestCase):
    def adapter(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.code_index.parsers.treesitter'), 'Optional language adapters missing')
        from aikya.code_index.parsers.treesitter import parse_file
        return parse_file

    def test_missing_optional_packages_fall_back_without_invented_symbols(self):
        parse = self.adapter()
        if importlib.util.find_spec('tree_sitter'):
            self.skipTest('Run fallback check in the dependency-free environment')
        result = parse('User.java', b'class User {}')
        self.assertEqual('file_only', result.status)
        self.assertEqual([], result.symbols)

    @unittest.skipUnless(importlib.util.find_spec('tree_sitter'), 'Optional parser extras not installed')
    def test_language_declarations_and_positions(self):
        parse = self.adapter()
        examples = [
            ('User.java', 'package demo; import java.util.List; class User { void save() {} }', {'demo.User', 'demo.User.save'}),
            ('user.js', 'export class User { save() {} }\nconst create = () => 1;', {'User', 'User.save', 'create'}),
            ('user.ts', 'interface Port { save(): void; }\nclass User { save(): void {} }', {'Port', 'Port.save', 'User', 'User.save'}),
            ('view.tsx', 'export function View() { return <main/>; }', {'View'}),
            ('User.cs', 'namespace Demo { public class User { public void Save() {} } }', {'Demo.User', 'Demo.User.Save'}),
            ('user.go', 'package demo\ntype User struct {}\nfunc (u User) Save() {}\nfunc Create() {}', {'User', 'User.Save', 'Create'}),
        ]
        for path, text, expected in examples:
            with self.subTest(path=path):
                result = parse(path, text.encode())
                self.assertEqual('indexed', result.status, result.diagnostics)
                self.assertEqual(expected, {s['qualified_name'] for s in result.symbols})
                for symbol in result.symbols:
                    self.assertGreater(symbol['end_byte'], symbol['start_byte'])
                    self.assertGreaterEqual(symbol['start_line'], 1)
                    self.assertLessEqual(symbol['end_byte'], len(text.encode()))
                self.assertFalse(any(e['relation'] == 'calls' for e in result.relations))

    @unittest.skipUnless(importlib.util.find_spec('tree_sitter'), 'Optional parser extras not installed')
    def test_syntax_errors_do_not_export_partial_classes_as_current(self):
        parse = self.adapter()
        result = parse('User.java', b'class User { public void broken(')
        self.assertEqual('parse_error', result.status)
        self.assertEqual([], result.symbols)

    def test_project_modules_cannot_impersonate_installed_grammars(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fake = root / 'tree_sitter';fake.mkdir()
            (fake / '__init__.py').write_text('from pathlib import Path\nPath("executed").write_text("bad")\nraise RuntimeError("project code executed")\n')
            dist = root / 'tree_sitter-0.25.2.dist-info';dist.mkdir()
            (dist / 'METADATA').write_text('Metadata-Version: 2.1\nName: tree-sitter\nVersion: 0.25.2\n')
            source = str(Path(__file__).resolve().parents[1] / 'src')
            script = 'import sys;sys.path.insert(0,sys.argv[1]);from aikya.code_index.parsers.treesitter import parse_file;assert parse_file("User.java",b"class User {}").status=="file_only"'
            result = subprocess.run([sys.executable, '-B', '-c', script, source], cwd=root, capture_output=True, text=True, timeout=10)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse((root / 'executed').exists())


if __name__ == '__main__':
    unittest.main()
