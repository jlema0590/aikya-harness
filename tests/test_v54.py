"""v5.4: renamed command bundle, conservative migration from prior Aikya installations."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aikya.installation import registration as aikya_setup
from aikya.installation import facade as install


class RenamedSkillsTests(unittest.TestCase):
    def test_source_exposes_registered_commands_without_legacy_directory(self):
        self.assertTrue((ROOT / 'src/aikya/resources/commands').is_dir())
        self.assertFalse((ROOT / 'bootstrap_skills').exists())
        for name in aikya_setup.BOOTSTRAP_COMMANDS:
            content = (ROOT / 'src/aikya/resources/commands' / name / 'SKILL.md').read_text(encoding='utf-8')
            self.assertIn('name: ' + name, content)

    def test_clean_project_and_global_scopes_use_new_runtime_layout(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            for scope in ('project', 'global'):
                with self.subTest(scope=scope):
                    home = base / scope / 'home'
                    project = base / scope / 'app'
                    logs = aikya_setup.setup(ROOT, project, scope, home=home)
                    runtime = home / '.claude/aikya-harnes' if scope == 'global' else project / '.aikya/runtime'
                    skills = home / '.claude/skills' if scope == 'global' else project / '.claude/skills'
                    self.assertTrue((runtime / 'aikya-skills/aikya-init/SKILL.md').is_file())
                    self.assertTrue((skills / 'aikya-init/SKILL.md').is_file())
                    self.assertFalse((runtime / 'bootstrap_skills').exists())
                    self.assertTrue(any('SKILL disponible: /aikya-init' in row for row in logs))

    def _simulate_old_layout(self, runtime: Path, names: list[str], with_custom: bool = False) -> Path:
        old = runtime / 'bootstrap_skills'
        state = json.loads((runtime / 'manifest.json').read_text(encoding='utf-8'))
        for name in names:
            data = (runtime / 'aikya-skills' / name / 'SKILL.md').read_bytes()
            path = old / name / 'SKILL.md'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            state['files'][path.relative_to(runtime).as_posix()] = hashlib.sha256(data).hexdigest()
        if with_custom:
            custom = old / 'aikya-feature' / 'custom-notes.md'
            custom.write_text('Never delete customer notes\n', encoding='utf-8')
            # A managed-looking skill with user modifications should not be removed.
            edited = old / 'aikya-feature' / 'SKILL.md'
            edited.write_text(edited.read_text() + '\nTEAM OVERRIDE\n', encoding='utf-8')
        (runtime / 'manifest.json').write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
        return old

    def test_migrate_managed_legacy_runtime_and_prune_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / 'app'
            aikya_setup.setup(ROOT, project, 'project')
            runtime = project / '.aikya/runtime'
            old = self._simulate_old_layout(runtime, ['aikya-init', 'aikya-skills-plan'])
            logs = aikya_setup.setup(ROOT, project, 'project')
            self.assertFalse(old.exists(), 'verified legacy dir should be removed')
            self.assertTrue((runtime / 'aikya-skills/aikya-init/SKILL.md').exists())
            state = json.loads((runtime / 'manifest.json').read_text())['files']
            self.assertFalse(any(k.startswith('bootstrap_skills/') for k in state))
            self.assertTrue(any('MIGRADO a aikya-skills/' in entry for entry in logs))
            self.assertEqual(logs.count('PRESERVED customized or unverified legacy asset'), 0)
            # Idempotency after migration.
            aikya_setup.setup(ROOT, project, 'project')
            self.assertFalse(old.exists())

    def test_preserves_customized_legacy_skill_and_extra_file(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / 'home'
            project = Path(temp) / 'app'
            aikya_setup.setup(ROOT, project, 'global', home=home)
            runtime = home / '.claude/aikya-harnes'
            old = self._simulate_old_layout(runtime, ['aikya-init', 'aikya-feature'], with_custom=True)
            logs = aikya_setup.setup(ROOT, project, 'global', home=home)
            self.assertFalse((old / 'aikya-init').exists())
            self.assertIn('TEAM OVERRIDE', (old / 'aikya-feature/SKILL.md').read_text())
            self.assertTrue((old / 'aikya-feature/custom-notes.md').exists())
            self.assertTrue((runtime / 'aikya-skills/aikya-feature/SKILL.md').is_file())
            self.assertTrue(any('PRESERVED customized or unverified legacy asset' in x for x in logs))

    def test_installer_still_initializes_project_skills_from_new_path(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / 'app'
            project.mkdir()
            answers = json.loads((ROOT / 'examples/new-next-react.json').read_text())
            profile = install.validated(answers, project)
            install.install(project, profile, {'modules': []})
            self.assertTrue((project / '.claude/skills/aikya-init/SKILL.md').exists())
            self.assertTrue((project / '.claude/skills/aikya-infra/SKILL.md').exists())


if __name__ == '__main__':
    unittest.main()
