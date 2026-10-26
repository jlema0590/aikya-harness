"""Run the executable support contracts behind every public Claude command."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aikya.cli.commands import BOOTSTRAP_COMMANDS


class CommandAcceptanceTests(unittest.TestCase):
    def test_all_public_commands_and_document_locations(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'results.json'
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/ci/command_acceptance.py'), '--output', str(output)],
                                    cwd=temporary, capture_output=True, text=True, timeout=180)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            report = json.loads(output.read_text())
            self.assertEqual(set(BOOTSTRAP_COMMANDS), set(report['commands']))
            self.assertTrue(report['valid'])
            self.assertFalse(report['live_model_execution'])
