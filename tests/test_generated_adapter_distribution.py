"""A source distribution must build without any source-root launchers."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec('build'), 'Build frontend is a contributor prerequisite')
class GeneratedAdapterDistribution(unittest.TestCase):
    def test_wheel_builds_without_root_adapters_and_contains_canonical_resources(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary); source = base / 'source'; source.mkdir()
            for name in ('setup.py', 'pyproject.toml', 'MANIFEST.in', 'VERSION', 'README.md', 'README.es.md', 'LICENSE', 'THIRD_PARTY_LICENSES.md', 'requirements-agent-loop.txt'):
                shutil.copy2(ROOT / name, source / name)
            shutil.copytree(ROOT / 'src', source / 'src', ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.egg-info'))
            (source / 'docs').mkdir()
            for name in ('AGENT_LOOP.md', 'SECURITY_CONTROLS.md'):
                shutil.copy2(ROOT / 'docs' / name, source / 'docs' / name)
            result = subprocess.run([sys.executable, '-m', 'build', '--wheel', '--no-isolation'], cwd=source, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr[-3000:])
            wheel = next((source / 'dist').glob('*.whl'))
            with zipfile.ZipFile(wheel) as archive:
                names = archive.namelist()
                self.assertIn('aikya/resources/compatibility/adapter.py.tmpl', names)
                self.assertIn('aikya/resources/compatibility/_aikya_bootstrap.py', names)
                self.assertFalse([name for name in names if name.startswith('aikya/resources/distribution/') and name.endswith('.py')])
            environment = base / 'environment'
            import venv
            venv.EnvBuilder(with_pip=True).create(environment)
            python = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
            installed = subprocess.run([str(python), '-m', 'pip', 'install', '--no-deps', '--no-index', str(wheel)], cwd=base, capture_output=True, text=True)
            self.assertEqual(0, installed.returncode, installed.stderr)
            target = base / 'project'; target.mkdir()
            command = 'from aikya.installation.registration import main;raise SystemExit(main())'
            result = subprocess.run([str(python), '-I', '-c', command, '--scope', 'project', '--target', str(target)], cwd=base, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr[-3000:])
            result = subprocess.run([str(python), '-B', str(target / '.aikya/runtime/aikya_cli.py'), '--help'], cwd=base, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            from agent_worker_support import install_sdk, assert_startup
            install_sdk(python)
            assert_startup(self, python, base)
