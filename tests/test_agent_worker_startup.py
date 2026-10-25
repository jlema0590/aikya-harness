"""Start the default SDK worker across actual package/adapter import contexts."""
import json
from pathlib import Path
import tempfile
import unittest

from agent_worker_support import ROOT, assert_startup, environment


class DefaultWorkerStartup(unittest.TestCase):
    def test_source_worker_starts_without_root_adapter_or_project_imports(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            assert_startup(self, environment(base), base, package_parent=ROOT / 'src')

    def test_missing_sdk_reports_blocked_instead_of_a_missing_worker_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            assert_startup(self, environment(base, sdk=False), base, package_parent=ROOT / 'src', sdk=False)

    def test_registered_global_and_project_workers_use_their_copied_package(self):
        from aikya.installation.registration import setup
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve(); python = environment(base)
            for scope in ('global', 'project'):
                with self.subTest(scope=scope):
                    target = base / scope; home = base / (scope + '-home')
                    setup(ROOT, target, scope, home=home)
                    runtime = home / '.claude/aikya-harnes' if scope == 'global' else target / '.aikya/runtime'
                    assert_startup(self, python, base, adapter=runtime / 'agent_runtime.py')

    def test_initialized_project_worker_uses_its_copied_package(self):
        from aikya.installation import facade
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve(); target = base / 'initialized'
            profile = facade.validated(json.loads((ROOT / 'examples/next-react/answers.json').read_text()), target)
            facade.install(target, profile, {'modules': [], 'findings': []}, docs_lang='en')
            assert_startup(self, environment(base), base, adapter=target / 'aikya/scripts/harness/agent_runtime.py')
