"""New generated plans, bugs and features must stay in the canonical docs tree."""
import runtime_support
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aikya.documentation import layout as docs_layout


def guard(root):
    spec = runtime_support.module_spec('path_policy_guard', ROOT / 'src/aikya/resources/project_template/scripts/harness/docs_guard.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module);module=getattr(module,'_module',module)
    module = getattr(module, '_module', module)
    module.ROOT = root
    module.STATE = root / '.harness/state'
    return getattr(module, '_module', module)


class DocumentPathPolicy(unittest.TestCase):
    def test_managed_runtime_templates_are_assets_not_misplaced_living_records(self):
        from aikya.installation import facade as install
        import json
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = install.validated(json.loads((ROOT / 'examples/next-react/answers.json').read_text()), root)
            install.install(root, profile, {'modules': []})
            name = 'aikya/scripts/harness/docs/AGENT_LOOP.md'
            self.assertEqual([], docs_layout.validate_generated_document_paths(root, [name]))

    def test_docs_only_ci_rejects_generated_records_outside_aikya_docs(self):
        for name in ('plans/change.md', 'plan/change.md', 'bugs/bug.md', 'features/change/spec.md', 'docs/research/report.md'):
            with self.subTest(path=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                file = root / name
                file.parent.mkdir(parents=True)
                file.write_text(docs_layout.stamp('# Reviewed record\n\nActual approved scope.'))
                ok, messages = guard(root).validate_ci([name])
                self.assertFalse(ok, messages)

    def test_stop_snapshot_detects_new_misplaced_record_without_code_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            module = guard(root)
            state = module.start_request('session', 'prepare a plan')
            file = root / 'plans/new.md'
            file.parent.mkdir()
            file.write_text(docs_layout.stamp('# Plan\n\nReviewed task scope.'))
            ok, messages = module.validate_request(state)
            self.assertFalse(ok, messages)

    def test_preserves_project_owned_docs_and_allows_canonical_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            owned = root / 'docs/api.md'
            owned.parent.mkdir()
            owned.write_text('# Owner API\n\nKeep this file.\n')
            docs_layout.write_document(root, 'features/value/spec.md', '# Value\n\nReviewed acceptance.')
            module = guard(root)
            ok, messages = module.validate_ci(['docs/api.md', 'aikya/docs/features/value/spec.md'])
            self.assertTrue(ok, messages)
            self.assertEqual('# Owner API\n\nKeep this file.\n', owned.read_text())
