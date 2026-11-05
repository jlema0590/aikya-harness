"""Use real registration in temporary homes; never modify personal skills."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aikya.installation.registration import setup, BOOTSTRAP_COMMANDS
from aikya.installation import facade

ROOT = Path(__file__).resolve().parents[1]


class CommandScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.home = self.base / 'home'
        self.home.mkdir()
        self.project = self.base / 'project'

    def tearDown(self):
        self.temp.cleanup()

    def global_setup(self):
        return setup(ROOT, self.project, 'global', home=self.home)

    def local_commands(self):
        return [p for p in (self.project / '.claude/skills').glob('aikya-*/SKILL.md')
                if p.parent.name in BOOTSTRAP_COMMANDS]

    def test_global_then_project_registration_does_not_duplicate_commands_or_runtime(self):
        self.global_setup()
        setup(ROOT, self.project, 'project', home=self.home)
        self.assertEqual([], self.local_commands())
        self.assertFalse((self.project / '.aikya/runtime').exists())
        self.assertTrue(all((self.home / '.claude/skills' / n / 'SKILL.md').is_file()
                            for n in BOOTSTRAP_COMMANDS))

    def test_global_then_onboarding_reuses_commands_and_keeps_project_policies(self):
        self.global_setup()
        profile = facade.validated({'name': 'scope-test', 'mode': 'new',
                                    'backend': 'none', 'frontend': 'react', 'methodology': 'odd'}, self.project)
        with patch('pathlib.Path.home', return_value=self.home):
            facade.install(self.project, profile, {'modules': [], 'findings': []})
        self.assertEqual([], self.local_commands())
        self.assertTrue((self.project / '.aikya/code-index.json').is_file())
        self.assertTrue((self.project / 'aikya/scripts/harness/aikya_cli.py').is_file())

    def test_local_registration_without_global_remains_standalone(self):
        setup(ROOT, self.project, 'project', home=self.home)
        self.assertEqual(len(BOOTSTRAP_COMMANDS), len(self.local_commands()))
        self.assertTrue((self.project / '.aikya/runtime/aikya_cli.py').is_file())

    def test_project_registration_retires_duplicates_after_global_update_with_backup(self):
        setup(ROOT, self.project, 'project', home=self.home)
        original = {p.parent.name: p.read_bytes() for p in self.local_commands()}
        self.global_setup()
        setup(ROOT, self.project, 'project', home=self.home)
        self.assertEqual([], self.local_commands())
        for name, raw in original.items():
            backups = list((self.project / '.harness').rglob(name + '/SKILL.md'))
            self.assertTrue(any(p.read_bytes() == raw for p in backups), name)
        self.assertTrue((self.project / '.aikya/runtime/aikya_cli.py').is_file())

    def test_customized_or_extended_local_skill_is_preserved(self):
        setup(ROOT, self.project, 'project', home=self.home)
        custom = self.project / '.claude/skills/aikya-init/SKILL.md'
        custom.write_text(custom.read_text() + '\nCustom team instructions\n')
        extra = self.project / '.claude/skills/aikya-docs/user-notes.txt'
        extra.write_text('preserve')
        before = custom.read_bytes()
        self.global_setup()
        setup(ROOT, self.project, 'project', home=self.home)
        self.assertEqual(before, custom.read_bytes())
        self.assertEqual('preserve', extra.read_text())
        self.assertEqual({'aikya-init', 'aikya-docs'}, {p.parent.name for p in self.local_commands()})

    def test_project_preview_does_not_create_or_retire_any_file(self):
        setup(ROOT, self.project, 'project', home=self.home)
        self.global_setup()
        before = {p.relative_to(self.base).as_posix(): p.read_bytes()
                  for p in self.base.rglob('*') if p.is_file()}
        setup(ROOT, self.project, 'project', home=self.home, dry_run=True)
        after = {p.relative_to(self.base).as_posix(): p.read_bytes()
                 for p in self.base.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_onboarding_upgrade_uses_pre_upgrade_provenance(self):
        profile = facade.validated({'name': 'scope-test', 'mode': 'existing',
                                    'frontend': 'react', 'methodology': 'odd'}, self.project)
        with patch('pathlib.Path.home', return_value=self.home):
            facade.install(self.project, profile, {'modules': [], 'findings': []})
        active = self.project / '.claude/skills/aikya-init/SKILL.md'
        old = active.read_bytes() + b'\nPrevious managed release instruction\n'
        active.write_bytes(old)
        runtime = self.project / 'aikya/scripts/harness'
        (runtime / 'aikya-skills/aikya-init/SKILL.md').write_bytes(old)
        manifest = runtime / '.bundle-manifest.json'
        data = json.loads(manifest.read_text())
        data['files']['aikya-skills/aikya-init/SKILL.md'] = hashlib.sha256(old).hexdigest()
        manifest.write_text(json.dumps(data))
        self.global_setup()
        with patch('pathlib.Path.home', return_value=self.home):
            facade.install(self.project, profile, {'modules': [], 'findings': []}, adopt_existing=True)
        self.assertFalse(active.exists())
        self.assertTrue(any(p.read_bytes() == old for p in (self.project / '.harness/command-backups').rglob('SKILL.md')))

    def test_matching_global_skill_without_runtime_provenance_is_not_reused(self):
        self.global_setup()
        (self.home / '.claude/aikya-harnes/.bundle-manifest.json').unlink()
        (self.home / '.claude/aikya-harnes/manifest.json').unlink()
        setup(ROOT, self.project, 'project', home=self.home)
        self.assertEqual(len(BOOTSTRAP_COMMANDS), len(self.local_commands()))

    def test_global_registration_does_not_scan_other_projects(self):
        other = self.base / 'other'
        setup(ROOT, other, 'project', home=self.home)
        self.global_setup()
        setup(ROOT, self.project, 'project', home=self.home)
        self.assertEqual(len(BOOTSTRAP_COMMANDS), len(list((other / '.claude/skills').glob('aikya-*/SKILL.md'))))

    def test_legacy_alias_can_retire_against_the_verified_global_replacement(self):
        setup(ROOT, self.project, 'project', home=self.home)
        old = self.project / '.claude/skills/aikya-project-init/SKILL.md'
        old.parent.mkdir()
        raw = (ROOT / 'tests/fixtures/command-renames/aikya-project-init.md').read_bytes()
        old.write_bytes(raw)
        self.global_setup()
        setup(ROOT, self.project, 'project', home=self.home)
        self.assertFalse(old.exists())
        self.assertTrue(any(p.read_bytes() == raw for p in (self.project / '.harness/command-backups').rglob('SKILL.md')))

    def test_analyze_preview_describes_global_reuse_without_local_command_creation(self):
        from aikya.discovery.analyze import installation_preview
        self.global_setup()
        self.project.mkdir()
        profile = facade.validated({'mode': 'existing', 'frontend': 'react', 'methodology': 'odd'}, self.project)
        with patch('pathlib.Path.home', return_value=self.home):
            rows = installation_preview(self.project, profile, {'modules': []})
        commands = [r for r in rows if r['path'].startswith('.claude/skills/aikya-')]
        self.assertEqual(len(BOOTSTRAP_COMMANDS), len(commands))
        self.assertTrue(all(r['action'] == 'REUSE_GLOBAL_COMMAND' for r in commands))
        self.assertFalse(any(self.project.iterdir()))

    def test_conflicting_backup_stops_before_retiring_any_commands(self):
        setup(ROOT, self.project, 'project', home=self.home)
        active = self.project / '.claude/skills/aikya-init/SKILL.md'
        backup = self.project / '.harness/command-backups' / hashlib.sha256(active.read_bytes()).hexdigest() / 'aikya-init/SKILL.md'
        backup.parent.mkdir(parents=True)
        backup.write_bytes(b'Existing owner backup')
        self.global_setup()
        before = {p.relative_to(self.project): p.read_bytes() for p in self.project.rglob('*') if p.is_file()}
        with self.assertRaises(ValueError):
            setup(ROOT, self.project, 'project', home=self.home)
        self.assertEqual(before, {p.relative_to(self.project): p.read_bytes() for p in self.project.rglob('*') if p.is_file()})

    def test_symlinked_command_stops_before_retiring_any_commands(self):
        setup(ROOT, self.project, 'project', home=self.home)
        active = self.project / '.claude/skills/aikya-init/SKILL.md'
        outside = self.base / 'owner.md'
        outside.write_bytes(active.read_bytes())
        active.unlink()
        try:
            active.symlink_to(outside)
        except OSError:
            self.skipTest('Symlink creation unavailable on this host')
        self.global_setup()
        before = {p.relative_to(self.project): p.read_bytes() for p in self.project.rglob('*') if p.is_file()}
        with self.assertRaises(ValueError):
            setup(ROOT, self.project, 'project', home=self.home)
        self.assertTrue(active.is_symlink())
        self.assertEqual(before, {p.relative_to(self.project): p.read_bytes() for p in self.project.rglob('*') if p.is_file()})
        self.assertEqual(before[active.relative_to(self.project)], outside.read_bytes())


if __name__ == '__main__':
    unittest.main()
