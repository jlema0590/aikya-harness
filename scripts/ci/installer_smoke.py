"""Exercise published installer payloads in disposable homes without a checkout."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def check(assets, python=sys.executable):
    results = []
    with tempfile.TemporaryDirectory(prefix='aikya-clean-') as temporary:
        base = Path(temporary).resolve() / "team's project"; base.mkdir()
        home = base / 'home'; home.mkdir(); project = base / 'project'; project.mkdir()
        app = base / 'application'
        env = {**os.environ, 'HOME': str(home), 'USERPROFILE': str(home), 'AIKYA_INSTALL_ROOT': str(app),
               'PYTHONPATH': '', 'PYTHONDONTWRITEBYTECODE': '1', 'AIKYA_EXECUTION_CACHE': str(base / 'cache')}
        env.pop('CLAUDE_PROJECT_DIR', None)
        settings = home / '.claude/settings.json'; settings.parent.mkdir()
        settings.write_text(json.dumps({'custom_setting': 'preserve', 'env': {'ANTHROPIC_AUTH_TOKEN': 'synthetic-do-not-copy'}}))
        document = project / 'owner.md'; document.write_text('# Owner document\n')
        payload = assets / 'aikya-bootstrap.pyz'
        version = next(assets.glob('aikya_harness-*-py3-none-any.whl')).name.removeprefix('aikya_harness-').removesuffix('-py3-none-any.whl')
        def run(argv, expected=0, input=None):
            process = subprocess.run([str(x) for x in argv], cwd=base, env=env, capture_output=True, text=True, timeout=240, input=input)
            if process.returncode != expected:
                raise ValueError(repr(argv) + '\n' + process.stderr[-4000:] + process.stdout[-2000:])
            return process
        for scope in ('global', 'project'):
            target = ['--target', project] if scope == 'project' else []
            arguments = ['--scope', scope, *target, '--offline-dir', assets, '--mods', 'none', '--no-path']
            if os.name == 'nt':
                command = ['powershell', '-NoProfile', '-File', assets / 'install.ps1', '-Scope', scope, '-Python', python, '-OfflineDir', assets, '-Mods', 'none', '-NoPath']
                if target:
                    command += ['-Target', project]
            else:
                command = ['/bin/sh', assets / 'install.sh', *arguments, '--python', python]
            run(command)
            current = json.loads((app / 'current.json').read_text()); installed_python = current['python']
            run([installed_python, '-I', '-B', '-m', 'aikya', '--help'])
            runtime = home / '.claude/aikya-harnes' if scope == 'global' else project / '.aikya/runtime'
            run([installed_python, '-B', runtime / 'aikya_cli.py', '--help'])
            run([installed_python, '-I', '-B', payload, 'update', '--version', version, *arguments])
            results.append({'scope': scope, 'entry_script': 'passed', 'runtime': 'passed', 'update': 'passed'})
        runtime = project / '.aikya/runtime'
        startup = json.loads((project / '.claude/settings.json').read_text())['hooks']['SessionStart'][0]['hooks'][0]
        shell = ['powershell', '-NoProfile', '-NonInteractive', '-Command'] if os.name == 'nt' else ['/bin/sh', '-c']
        run([*shell, startup['command']], input=json.dumps({'source': 'startup', 'cwd': str(project)}))
        initialized = base / 'initialized'; initialized.mkdir()
        answers = base / 'answers.json'
        answers.write_text(json.dumps({'mode': 'new', 'name': 'clean-app', 'project_type': 'development', 'backend': 'next',
                                       'backend_framework': 'next-app-router', 'frontend': 'react', 'mobile': 'none', 'repository_layout': 'singlerepo'}))
        run([installed_python, '-B', runtime / 'aikya_cli.py', 'init', '--target', initialized, '--answers', answers,
             '--methodology', 'odd', '--docs-lang', 'en', '--external', 'skip'])
        existing = base / 'existing'; existing.mkdir(); (existing / 'pom.xml').write_text('<project/>')
        run([installed_python, '-B', runtime / 'aikya_cli.py', 'analyze', '--target', existing, '--approved', '--methodology', 'sdd', '--docs-lang', 'es'])
        for target in (initialized, existing):
            run([installed_python, '-B', target / 'aikya/scripts/harness/docs_guard.py', 'base'])
            assert (target / 'aikya/docs/indice.md').is_file()
            assert not any((target / name).exists() for name in ('docs', 'plans', 'features', 'bugs'))
        # Detect credential copies even when the receipt encodes entire files.
        def inspect(value):
            if isinstance(value, str):
                assert 'synthetic-do-not-copy' not in value
                try:
                    decoded = base64.b64decode(value, validate=True)
                except ValueError:
                    return
                assert b'synthetic-do-not-copy' not in decoded
            elif isinstance(value, dict):
                for child in value.values(): inspect(child)
            elif isinstance(value, list):
                for child in value: inspect(child)
        for record in (app / 'receipts').glob('*.json'):
            inspect(json.loads(record.read_text()))
        # Remove one registration while another still requires its interpreter.
        for scope in ('global', 'project'):
            target = ['--target', project] if scope == 'project' else []
            run([python, '-I', '-B', payload, 'uninstall', '--scope', scope, *target])
        assert json.loads(settings.read_text()) == {'custom_setting': 'preserve', 'env': {'ANTHROPIC_AUTH_TOKEN': 'synthetic-do-not-copy'}}
        assert document.read_text() == '# Owner document\n'
        assert not (app / 'current.json').exists()
        assert (app / 'versions').is_dir(), 'Initialized projects lost their referenced interpreter'
        run([installed_python, '-B', initialized / 'aikya/scripts/harness/docs_guard.py', 'base'])
        assert not (project / 'docs').exists() and not (project / 'plans').exists()
    return {'platform': sys.platform, 'python': sys.version.split()[0], 'cases': results,
            'uninstall_preserved_user_files': True, 'checkout_required': False, 'live_model': False, 'initialization': ['new/odd/en', 'existing/sdd/es'], 'referenced_interpreters_retained': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = check(args.assets.resolve())
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
