"""Default installs resolve one stable release without losing explicit/offline pins."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from aikya.installation.bootstrap import cli, download

ROOT = Path(__file__).resolve().parents[1]
LATEST = 'https://api.github.com/repos/jlema0590/aikya-harness/releases/latest'


def metadata(**changes):
    return json.dumps(dict(tag_name='v7.2.3', draft=False, prerelease=False,
                           published_at='2026-10-25T10:00:00Z', **changes)).encode()


class LatestReleaseSelection(unittest.TestCase):
    def test_install_and_update_default_to_published_stable_release_without_writes(self):
        for action in ('install', 'update'):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve(); project = base / 'project'; project.mkdir()
                requests = []
                def read(url, limit):
                    requests.append((url, limit))
                    if url != LATEST:
                        raise AssertionError('Unexpected request: ' + url)
                    return metadata()
                output = io.StringIO()
                with patch.dict(os.environ, {'AIKYA_INSTALL_ROOT': str(base / 'app')}), patch.object(download, 'https_bytes', side_effect=read), contextlib.redirect_stdout(output):
                    result = cli.main([action, '--scope', 'project', '--target', str(project), '--dry-run'])
                self.assertEqual(0, result)
                self.assertEqual('7.2.3', json.loads(output.getvalue())['version'])
                self.assertEqual([(LATEST, 1024 * 1024)], requests)
                self.assertFalse((base / 'app').exists())
                self.assertEqual([], list(project.iterdir()))

    def test_latest_alias_resolves_once_then_downloads_only_selected_version(self):
        requests = []
        wheel_name = 'aikya_harness-7.2.3-py3-none-any.whl'
        wheel_bytes = b'controlled-verified-wheel'
        manifest = (hashlib.sha256(wheel_bytes).hexdigest() + '  ' + wheel_name + '\n').encode()
        responses = {
            LATEST: metadata(),
            'https://github.com/jlema0590/aikya-harness/releases/download/v7.2.3/SHA256SUMS': manifest,
            'https://github.com/jlema0590/aikya-harness/releases/download/v7.2.3/' + wheel_name: wheel_bytes,
        }
        def read(url, limit=download.LIMIT):
            requests.append(url)
            return responses[url]
        with tempfile.TemporaryDirectory() as temporary, patch.object(download, 'https_bytes', side_effect=read):
            version = download.resolve_version('latest')
            assets = download.fetch_release(version, Path(temporary) / 'download')
            self.assertEqual(wheel_bytes, assets['wheel'].read_bytes())
        self.assertEqual(list(responses), requests)

    def test_explicit_numeric_version_never_queries_latest(self):
        with patch.object(download, 'https_bytes', side_effect=AssertionError('Network forbidden')):
            self.assertEqual('7.0.1', download.resolve_version('7.0.1'))
            self.assertEqual('7.0.1', download.resolve_version('7.0.1', Path('/offline')))

    def test_bad_latest_metadata_and_network_failures_do_not_provision(self):
        valid = json.loads(metadata())
        invalid = [b'not json', b'[]', b'null']
        for changes in ({'draft': True}, {'prerelease': True}, {'draft': 'false'},
                        {'published_at': None}, {'tag_name': 'v7.2.3-rc1'},
                        {'tag_name': 'main'}, {'tag_name': 'v07.2.3'},
                        {'tag_name': '../7.2.3'}, {'tag_name': None}):
            invalid.append(json.dumps({**valid, **changes}).encode())
        invalid.append(json.dumps({'tag_name': 'v7.2.3'}).encode())
        for response in [*invalid, OSError('release unavailable')]:
            with self.subTest(response=response), tempfile.TemporaryDirectory() as temporary:
                app = Path(temporary).resolve() / 'app'
                effect = {'side_effect': response} if isinstance(response, Exception) else {'return_value': response}
                with patch.dict(os.environ, {'AIKYA_INSTALL_ROOT': str(app)}), patch.object(download, 'https_bytes', **effect), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(2, cli.main(['install', '--scope', 'global', '--dry-run']))
                self.assertFalse(app.exists())

    def test_offline_latest_requires_numeric_version_without_network_or_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            for version in ([], ['--version', 'latest']):
                with self.subTest(version=version), patch.dict(os.environ, {'AIKYA_INSTALL_ROOT': str(base / 'app')}), patch.object(download, 'https_bytes', side_effect=AssertionError('Network forbidden')), contextlib.redirect_stderr(io.StringIO()) as errors:
                    self.assertEqual(2, cli.main(['install', '--scope', 'global', '--offline-dir', str(base), '--dry-run', *version]))
                self.assertIn('--version', errors.getvalue())
                self.assertFalse((base / 'app').exists())

    def test_latest_endpoint_is_https_allowlisted_and_insecure_redirects_are_rejected(self):
        download.validate_url(LATEST)
        for url in ('http://api.github.com/repos/x', 'https://evil.example/latest',
                    'https://user@api.github.com/repos/x'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                download.validate_url(url)


class LatestEntryScripts(unittest.TestCase):
    def build(self, base):
        assets = base / 'release'
        subprocess.run([sys.executable, str(ROOT / 'scripts/ci/build_installers.py'), '--version', '7.0.1', '--output', str(assets)], check=True, capture_output=True, text=True)
        return assets

    @unittest.skipIf(os.name == 'nt', 'POSIX entry script')
    def test_shell_online_defaults_to_latest_and_preserves_explicit_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve(); assets = self.build(base)
            # Substitute only download/process boundaries; run the real rendered shell script.
            binary = base / 'bin'; binary.mkdir()
            curl = binary / 'curl'
            curl.write_text('#!' + sys.executable + '\nimport os,shutil,sys\n'
                            'assert "https://github.com/jlema0590/aikya-harness/releases/download/v7.0.1/aikya-bootstrap.pyz" in sys.argv\n'
                            'shutil.copyfile(os.environ["TEST_PAYLOAD"], sys.argv[sys.argv.index("-o")+1])\n')
            curl.chmod(0o755)
            python = binary / 'test-python'
            python.write_text('#!' + sys.executable + '\nimport json,os,sys\n'
                              'if "-c" not in sys.argv and any(x.endswith(".pyz") for x in sys.argv):\n'
                              ' print(json.dumps(sys.argv[1:]));sys.exit(0)\n'
                              'os.execv(sys.executable,[sys.executable,*sys.argv[1:]])\n')
            python.chmod(0o755)
            env = {**os.environ, 'PATH': str(binary) + os.pathsep + os.environ['PATH'],
                   'TEST_PAYLOAD': str(assets / 'aikya-bootstrap.pyz')}
            for version in ([], ['--version', '7.1.2']):
                with self.subTest(version=version):
                    result = subprocess.run(['/bin/sh', str(assets / 'install.sh'), '--scope', 'global', '--python', str(python), '--dry-run', *version], env=env, capture_output=True, text=True)
                    self.assertEqual(0, result.returncode, result.stderr)
                    args = json.loads(result.stdout)
                    self.assertEqual(version, args[args.index('--version'):] if '--version' in args else [])

    def test_native_script_offline_defaults_to_its_release_and_accepts_override(self):
        powershell = shutil.which('powershell') or shutil.which('pwsh')
        if os.name == 'nt' and not powershell:
            self.fail('Native Windows requires PowerShell for installer acceptance')
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve(); assets = self.build(base)
            env = {**os.environ, 'AIKYA_INSTALL_ROOT': str(base / 'app'), 'HOME': str(base / 'home'), 'USERPROFILE': str(base / 'home')}
            for version in (None, '7.1.2'):
                if os.name == 'nt':
                    argv = [powershell, '-NoProfile', '-File', str(assets / 'install.ps1'), '-Scope', 'global', '-Python', sys.executable, '-OfflineDir', str(assets), '-DryRun']
                    if version:
                        argv += ['-Version', version]
                else:
                    argv = ['/bin/sh', str(assets / 'install.sh'), '--scope', 'global', '--python', sys.executable, '--offline-dir', str(assets), '--dry-run']
                    if version:
                        argv += ['--version', version]
                with self.subTest(version=version):
                    result = subprocess.run(argv, env=env, cwd=base, capture_output=True, text=True)
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual(version or '7.0.1', json.loads(result.stdout)['version'])
                    self.assertFalse((base / 'app').exists())

    @unittest.skipUnless(shutil.which('powershell') or shutil.which('pwsh'), 'PowerShell is required')
    def test_powershell_verifies_bootstrap_without_get_filehash_and_rejects_corruption(self):
        powershell = shutil.which('powershell') or shutil.which('pwsh')
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve(); assets = self.build(base)
            driver = base / 'driver.ps1'
            driver.write_text('param([string]$Installer,[string]$Python,[string]$Assets)\n'
                              '$PSNativeCommandArgumentPassing = "Legacy"\n'
                              'function global:Get-FileHash { throw "Get-FileHash is unavailable" }\n'
                              '& $Installer -Scope global -Python $Python -OfflineDir $Assets -DryRun\n')
            env = {**os.environ, 'AIKYA_INSTALL_ROOT': str(base / 'app'), 'HOME': str(base / 'home'), 'USERPROFILE': str(base / 'home')}
            command = [powershell, '-NoProfile', '-File', str(driver), '-Installer', str(assets / 'install.ps1'), '-Python', sys.executable, '-Assets', str(assets)]
            result = subprocess.run(command, env=env, cwd=base, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual('7.0.1', json.loads(result.stdout)['version'])
            (assets / 'aikya-bootstrap.pyz').write_bytes(b'corrupt bootstrap')
            result = subprocess.run(command, env=env, cwd=base, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn('checksum mismatch', result.stderr)
            self.assertFalse((base / 'app').exists())
