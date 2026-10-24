"""Repository consumers must not require retired source-root Python aliases."""
import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SourceConsumers(unittest.TestCase):
    def test_current_python_consumers_import_canonical_modules(self):
        aliases = set(json.loads((ROOT / 'src/aikya/module_map.json').read_text()))
        violations = []
        for folder in ('tests', 'scripts/ci'):
            for path in (ROOT / folder).glob('*.py'):
                for node in ast.walk(ast.parse(path.read_text())):
                    names = [item.name for item in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) else []
                    for name in names:
                        if name in aliases:
                            violations.append(f'{path.relative_to(ROOT)}:{node.lineno}:{name}')
        self.assertEqual([], violations, '\n'.join(violations))
