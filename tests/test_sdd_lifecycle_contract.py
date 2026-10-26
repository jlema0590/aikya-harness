"""Byte-level lifecycle characterization captured before splitting the SDD engine."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aikya.installation import facade as install
from aikya.workflows.sdd import engine as sdd


def lifecycle_fingerprints(root, kind, language):
    example, dossier = {'development': ('next-react', 'order-api'),
                        'infrastructure': ('infra-terraform-only', 'aws-network'),
                        'devops': ('devops-kustomize', 'kubernetes-release')}[kind]
    profile = install.validated({**json.loads((ROOT / 'examples' / example / 'answers.json').read_text()), 'methodology': 'sdd'}, root)
    path = root / '.harness/project-profile.json'; path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'decisions': profile}))
    path = root / '.aikya/docs-policy.json'; path.parent.mkdir()
    path.write_text(json.dumps({'schema_version': 1, 'language': language}))
    folder = ROOT / 'examples/sdd' / kind / dossier
    inputs = {name: json.loads((folder / (name + '.json')).read_text()) for name in ('spec', 'clarify', 'plan', 'tasks')}
    result = {}
    def snapshot(stage, output):
        files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in root.rglob('*') if p.is_file() and (p.suffix == '.md' or p.name == 'state.json')}
        raw = json.dumps({'output': output, 'files': files}, sort_keys=True, ensure_ascii=False).encode()
        result[stage] = hashlib.sha256(raw).hexdigest()
    snapshot('new', sdd.initialize(root, inputs['spec']))
    snapshot('clarify', sdd.clarify(root, 'SPEC-001', inputs['clarify']))
    snapshot('approve-spec', sdd.approve(root, 'SPEC-001', 'spec', 'controlled-reviewer'))
    snapshot('plan', sdd.create_plan(root, 'SPEC-001', inputs['plan']))
    snapshot('approve-plan', sdd.approve(root, 'SPEC-001', 'plan', 'controlled-reviewer'))
    snapshot('tasks', sdd.create_tasks(root, 'SPEC-001', inputs['tasks']))
    snapshot('approve-tasks', sdd.approve(root, 'SPEC-001', 'tasks', 'controlled-reviewer'))
    check = subprocess.run([sys.executable, '-c', "print('Controlled fixture check passed')"], capture_output=True, text=True, check=True)
    path = root / '.harness/refactor-check.log'; path.write_text(check.stdout)
    tasks = sdd.load(root, 'SPEC-001')[1]['tasks']
    for task in tasks:
        snapshot('progress-' + task['id'], sdd.progress(root, 'SPEC-001', task['id'], 'done', '.harness/refactor-check.log'))
    reqs = inputs['spec']['requirements']
    snapshot('verify', sdd.verify(root, 'SPEC-001', {'requirements': [
        {'id': req['id'], 'result': 'passed', 'command': 'controlled local Python fixture', 'evidence': '.harness/refactor-check.log'} for req in reqs]}))
    snapshot('review', sdd.create_document(root, 'review', {'sections': {'decision': 'Controlled fixture reviewed.'}}, ident='SPEC-001', approved=True))
    snapshot('constitution', sdd.create_document(root, 'constitution', {'sections': {'principles': 'Keep controlled fixture changes scoped.'}}, approved=True))
    snapshot('completion', sdd.validate_completion(root, 'SPEC-001'))
    snapshot('lint', sdd.validate(root))
    return result


class SddLifecycleContractTests(unittest.TestCase):
    def test_three_types_and_two_locales_match_pre_refactor_documents_and_results(self):
        expected = json.loads((ROOT / 'tests/fixtures/sdd-lifecycle-contracts.json').read_text())['cases']
        for kind in ('development', 'infrastructure', 'devops'):
            for language in ('en', 'es'):
                with self.subTest(kind=kind, language=language), tempfile.TemporaryDirectory() as temporary:
                    self.assertEqual(expected[kind + '-' + language], lifecycle_fingerprints(Path(temporary), kind, language))
