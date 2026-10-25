"""Disposable SDK boundary and assertions shared by source/wheel startup tests."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]


def environment(base, *, sdk=True):
    target = base / 'environment'
    venv.EnvBuilder(with_pip=False).create(target)
    python = target / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if sdk:
        install_sdk(python)
    return python


def install_sdk(python):
    result = subprocess.run([str(python), '-I', '-c', 'import sysconfig;print(sysconfig.get_path("purelib"))'], check=True, capture_output=True, text=True)
    site = Path(result.stdout.strip())
    sdk = site / 'claude_agent_sdk'; sdk.mkdir()
    shutil.copy2(ROOT / 'tests/fixtures/agent-loop/sdk_standin.py', sdk / '__init__.py')
    metadata = site / 'claude_agent_sdk-0.2.173.dist-info'; metadata.mkdir()
    (metadata / 'METADATA').write_text('Metadata-Version: 2.1\nName: claude-agent-sdk\nVersion: 0.2.173\n')


def assert_startup(test, python, base, *, package_parent=None, adapter=None, sdk=True):
    cwd = base / 'unrelated'; cwd.mkdir(exist_ok=True)
    shadow = cwd / 'aikya'; shadow.mkdir(exist_ok=True)
    (shadow / '__init__.py').write_text('raise RuntimeError("untrusted project import")\n')
    (cwd / 'agent_runtime.py').write_text('raise RuntimeError("retired project shadow")\n')
    if adapter:
        load = 'sys.path.insert(0,' + repr(str(adapter.parent)) + ');import agent_runtime as runtime;'
        expected = adapter.parent / 'src/aikya/core/runtime.py'
    else:
        load = ('sys.path.insert(0,' + repr(str(package_parent)) + ');') if package_parent else ''
        load += 'import aikya.core.runtime as runtime;'
        expected = package_parent / 'aikya/core/runtime.py' if package_parent else None
    driver = ('import json,subprocess,sys;' + load + 'worker=runtime.ProcessRuntime();'
              'args=json.loads(sys.argv[1]);'
              'result=subprocess.run(worker.command[:-1]+["check"] if args["mode"]=="check" else worker.command,input=args.get("input"),capture_output=True,text=True,timeout=10);'
              'print(json.dumps({"module":runtime.__file__,"exit":result.returncode,"stdout":result.stdout,"stderr":result.stderr}))')
    env = {**os.environ, 'PYTHONPATH': str(cwd), 'PYTHONDONTWRITEBYTECODE': '1'}
    requests = [{'mode': 'check'}]
    if sdk:
        for phase in ('review', 'extract'):
            request = {'root': str(cwd), 'files': [], 'context_files': [], 'phase': phase,
                       'max_turns': 2, 'remaining_cost_usd': 0.01, 'prompt': 'Offline startup contract.'}
            requests.append({'mode': phase, 'input': json.dumps(request) + '\n'})
    for request in requests:
        result = subprocess.run([str(python), '-I', '-B', '-c', driver, json.dumps(request)], cwd=cwd, env=env, capture_output=True, text=True, timeout=20)
        test.assertEqual(0, result.returncode, result.stderr)
        observed = json.loads(result.stdout)
        if expected:
            test.assertEqual(expected.resolve(), Path(observed['module']).resolve())
        test.assertEqual(0 if sdk else 4, observed['exit'], observed['stderr'])
        if request['mode'] == 'check':
            test.assertEqual({'available': True, 'sdk_version': '0.2.173'} if sdk else {'available': False, 'reason': 'optional_sdk_missing'}, json.loads(observed['stdout']))
        else:
            events = [json.loads(line) for line in observed['stdout'].splitlines()]
            test.assertEqual('model', events[0]['type'])
            test.assertEqual('result', events[-1]['type'])
            test.assertFalse(events[-1]['error'])
            test.assertEqual({'candidates': []} if request['mode'] == 'extract' else {'status': 'done', 'approved': True}, events[-1]['output'])
