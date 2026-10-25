"""v6 regression tests: no false documentation gating and bounded context."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/aikya/resources/project_template/scripts/harness'))
sys.path.insert(0, str(ROOT))

from aikya.documentation.guard import kind_from_prompt
from aikya.quality.context_budget import estimate

class V6ContextTests(unittest.TestCase):
    def test_false_positive_substrings(self):
        self.assertEqual(kind_from_prompt("prefix y recrear son nombres de variables"), "general")
        self.assertEqual(kind_from_prompt("¿Qué error da este código?"), "general")
        self.assertEqual(kind_from_prompt("¿Qué hace Docker?"), "general")

    def test_action_is_classified(self):
        self.assertIn("bug", kind_from_prompt("corrige el error del login"))
        self.assertIn("operations", kind_from_prompt("revisa pipeline Docker"))

    def test_context_budget_is_observable(self):
        report = estimate(ROOT / 'src/aikya/resources/project_template')
        self.assertGreater(report["proxy_tokens"], 0)
        self.assertLess(report["proxy_tokens"], 6000)
        self.assertIn("disclaimer", report)

if __name__ == "__main__":
    unittest.main()
