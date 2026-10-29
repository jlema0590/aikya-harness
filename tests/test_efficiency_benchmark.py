import importlib.util
from pathlib import Path
import unittest

class BenchmarkTests(unittest.TestCase):
    def test_offline_contract_never_claims_real_token_or_quota_savings(self):
        path=Path(__file__).resolve().parents[1]/'scripts/ci/token_efficiency_benchmark.py'
        self.assertTrue(path.is_file(),'Missing reproducible efficiency benchmark')
        spec=importlib.util.spec_from_file_location('efficiency_benchmark',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        report=module.benchmark()
        self.assertFalse(report['live_model_execution']);self.assertIsNone(report['quota_savings'])
        self.assertEqual(report['command_count'],28)
        self.assertEqual(len(report['languages']),29)
        self.assertTrue(report['valid'])
        self.assertTrue(all(row['tokens'] is None for row in report['commands'].values()))

if __name__=='__main__':unittest.main()
