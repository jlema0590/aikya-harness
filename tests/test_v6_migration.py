import json
import tempfile
import unittest
from pathlib import Path

from aikya.installation import facade as install
from aikya.routing.policy import validated, HAIKU_45, HAIKU_55

ROOT = Path(__file__).resolve().parents[1]

class V6InstallerMigrationTests(unittest.TestCase):
    def profile(self, root):
        answers = json.loads((ROOT/"examples/new-next-react.json").read_text())
        return install.validated(answers, root)

    def test_v1_policy_is_not_changed_by_reinstall(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            profile = self.profile(root)
            (root/".aikya").mkdir()
            policy_file = root/".aikya/model-policy.json"
            old = {"schema_version": 1, "auxiliary_model": HAIKU_45,
                   "auxiliary_enabled": True, "user_approved": True}
            policy_file.write_text(json.dumps(old)+"\n")
            before = policy_file.read_bytes()
            install.install(root, profile, {"modules":[]})
            self.assertEqual(before, policy_file.read_bytes())
            self.assertEqual(
                json.loads((root/".harness/project-profile.json").read_text())["schema_version"], 1)

    def test_fresh_install_disables_auxiliary_models(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            install.install(root, self.profile(root), {"modules":[]})
            policy = validated(json.loads((root/".aikya/model-policy.json").read_text()))
            self.assertEqual(policy["schema_version"], 2)
            self.assertEqual(policy["auxiliary_model"], HAIKU_55)
            self.assertFalse(policy["auxiliary_enabled"])
            for file in ("token_policy.py", "token_report.py",
                         "model_capabilities.py", "aikya_router.py"):
                self.assertTrue((root/"aikya/scripts/harness"/file).is_file())
            self.assertFalse((root/".claude/agents/aikya-auxiliary-analyzer.md").exists())

if __name__ == "__main__":
    unittest.main()
