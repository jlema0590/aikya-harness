"""Package execution must work without the source checkout on the import path."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PackageContracts(unittest.TestCase):
    def test_runtime_inventory_excludes_private_environment_files_and_unrelated_package_data(self):
        import shutil
        from aikya.installation import registration as aikya_setup
        from aikya.installation.assets import runtime_assets
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            shutil.copytree(ROOT / 'src/aikya', source / 'src/aikya', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            for name in ('requirements-agent-loop.txt','docs/AGENT_LOOP.md','docs/SECURITY_CONTROLS.md'):
                destination = source / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, destination)
            (source / 'src/aikya/.env').write_text('Synthetic private fixture\n')
            (source / 'src/aikya/private-notes.txt').write_text('Synthetic private fixture\n')
            template = source / 'src/aikya/resources/project_template'
            (template / '.env').write_text('Synthetic private fixture\n')
            (template / '.env.example').write_text('# Placeholder only\n')
            paths = {asset.destination.as_posix() for asset in runtime_assets(source, 'registration')}
            self.assertNotIn('src/aikya/.env', paths)
            self.assertNotIn('src/aikya/private-notes.txt', paths)
            self.assertNotIn('template/.env', paths)
            self.assertIn('template/.env.example', paths)

    def test_customized_package_blocks_upgrade_before_launchers_change(self):
        from aikya.installation import registration as aikya_setup
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'project'
            home = Path(temporary) / 'home'
            aikya_setup.setup(ROOT, target, 'project', home=home)
            runtime = target / '.aikya/runtime'
            file = runtime / 'src/aikya/documentation/layout.py'
            file.write_text(file.read_text() + '\n# Owner customization.\n')
            launcher = runtime / 'aikya_cli.py'
            before = launcher.read_bytes()
            with self.assertRaisesRegex(ValueError, 'Customized|customized'):
                aikya_setup.setup(ROOT, target, 'project', home=home)
            self.assertEqual(before, launcher.read_bytes())
            self.assertIn('# Owner customization.', file.read_text())

    def test_package_cli_and_resources_from_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            env = {**os.environ, 'PYTHONPATH': str(ROOT / 'src')}
            result = subprocess.run([sys.executable, '-B', '-m', 'aikya', '--help'], cwd=temporary, env=env, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn('analyze', result.stdout)
            code = "from aikya.resource_paths import source_root,source_path;from aikya.documentation.templates import catalog;assert source_path(source_root(),'template/CLAUDE.md').is_file();assert source_path(source_root(),'aikya-template/docs/LICENSE').is_file();assert len(catalog())==120"
            result = subprocess.run([sys.executable, '-B', '-c', code], cwd=temporary, env=env, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)

    def test_installed_legacy_import_and_package_share_the_same_mutable_module(self):
        from aikya.installation.registration import setup
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            setup(ROOT, target, 'project', home=target / 'home')
            code = "import sys;sys.path.insert(0," + repr(str(target / '.aikya/runtime')) + ");import docs_layout;from aikya.documentation import layout;assert docs_layout is layout;import install;from aikya.installation import facade;assert install is facade"
            result = subprocess.run([sys.executable, '-B', '-c', code], cwd=temporary, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)

    def test_installer_dry_run_leaves_target_untouched(self):
        from aikya.installation import facade as install
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'new'
            profile = install.validated(json.loads((ROOT / 'examples/next-react/answers.json').read_text()), target)
            actions = install.install(target, profile, {'modules': [], 'findings': []}, dry_run=True)
            self.assertTrue(actions)
            self.assertFalse(target.exists())
