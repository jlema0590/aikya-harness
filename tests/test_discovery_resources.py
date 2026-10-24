"""Bounded provider discovery must close every inspected file."""
from pathlib import Path
import sys
import tempfile
import unittest
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aikya.discovery import scanner as project_discovery


class DiscoveryResourceTests(unittest.TestCase):
    def test_terraform_provider_probe_closes_its_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'main.tf').write_text('provider "aws" {}\n')
            with warnings.catch_warnings(record=True) as observed:
                warnings.simplefilter('always', ResourceWarning)
                result = project_discovery.scan(root)
            self.assertEqual([], [w for w in observed if issubclass(w.category, ResourceWarning)])
            self.assertIn('aws', str(result))
