"""Regression contracts for SDD integration with current develop."""
import runtime_support
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aikya.workflows.sdd import engine as sdd
from aikya.installation import facade as install
from aikya.documentation import bootstrap as doc_bootstrap
from aikya.installation import registration as aikya_setup


def module(name, relative):
    from aikya.resource_paths import source_path
    spec = runtime_support.module_spec(name, source_path(ROOT,relative))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result);result=getattr(result,'_module',result)
    return result


class SddIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.profile = {'project_type': 'development', 'methodology': 'sdd'}
        p = self.root / '.harness/project-profile.json'
        p.parent.mkdir()
        p.write_text(json.dumps({'decisions': self.profile}))
        self.fixture = ROOT / 'examples/sdd/development/order-api'
        self.inputs = {k: json.loads((self.fixture / (k + '.json')).read_text())
                       for k in ('spec', 'clarify', 'plan', 'tasks')}

    def ready(self):
        sdd.initialize(self.root, self.inputs['spec'])
        sdd.clarify(self.root, 'SPEC-001', self.inputs['clarify'])
        sdd.approve(self.root, 'SPEC-001', 'spec', 'reviewer')
        sdd.create_plan(self.root, 'SPEC-001', self.inputs['plan'])
        sdd.approve(self.root, 'SPEC-001', 'plan', 'reviewer')
        sdd.create_tasks(self.root, 'SPEC-001', self.inputs['tasks'])
        sdd.approve(self.root, 'SPEC-001', 'tasks', 'reviewer')
        return self.root / 'aikya/docs/specs/development/SPEC-001/state.json'

    def mutate(self, change):
        path = self.ready()
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data))
        return path

    def test_lint_rejects_unknown_requirement_after_state_edit(self):
        self.mutate(lambda d: d['tasks'][0].update(requirements=['REQ-999']))
        self.assertFalse(sdd.validate(self.root)['valid'])

    def test_lint_rejects_unknown_dependency_after_state_edit(self):
        self.mutate(lambda d: d['tasks'][0].update(depends_on=['TASK-999']))
        self.assertFalse(sdd.validate(self.root)['valid'])

    def test_lint_rejects_cycle_after_state_edit(self):
        self.mutate(lambda d: d['tasks'][0].update(depends_on=['TASK-001']))
        self.assertFalse(sdd.validate(self.root)['valid'])

    def test_load_rejects_missing_requirement_coverage(self):
        self.mutate(lambda d: d['spec']['requirements'].append(
            {'id': 'REQ-002', 'description': 'Another requirement', 'acceptance': ['Checked']}))
        with self.assertRaises(sdd.SddError):
            sdd.load(self.root, 'SPEC-001')

    def test_false_approval_is_not_approved(self):
        self.assertFalse(sdd.approvals_done({'approvals': {'tasks': {'approved': False}}}, 'tasks'))

    def test_load_rejects_invalid_approval_order(self):
        self.mutate(lambda d: d['approvals'].pop('spec'))
        with self.assertRaises(sdd.SddError):
            sdd.load(self.root, 'SPEC-001')

    def test_old_spec_cannot_unlock_scaffold_without_active_context(self):
        self.ready()
        scaffold = module('sdd_scope_scaffold', 'template/scripts/harness/scaffold.py')
        self.assertFalse(scaffold.sdd_approved(self.root, self.profile))

    def test_old_spec_cannot_unlock_infrastructure_without_active_context(self):
        self.ready()
        infra = module('sdd_scope_infra', 'template/scripts/harness/infrastructure.py')
        self.assertFalse(infra.sdd_approved(self.root, self.profile))

    def test_pending_spec_cannot_use_previous_spec_approval(self):
        self.ready()
        sdd.initialize(self.root, {**self.inputs['spec'], 'id': 'SPEC-002'})
        self.assertTrue(callable(getattr(sdd, 'require_approved_task', None)))
        with self.assertRaises(sdd.SddError):
            sdd.require_approved_task(self.root, 'SPEC-002', 'TASK-001')
        self.assertEqual('TASK-001', sdd.require_approved_task(self.root, 'SPEC-001', 'TASK-001')['id'])

    def test_draft_is_structurally_valid_but_not_complete(self):
        sdd.initialize(self.root, self.inputs['spec'])
        self.assertTrue(sdd.validate(self.root)['valid'])
        self.assertTrue(callable(getattr(sdd, 'validate_completion', None)))
        self.assertTrue(sdd.validate_completion(self.root, 'SPEC-001'))

    def test_completion_requires_passing_recorded_evidence(self):
        self.ready()
        (self.root / 'evidence.txt').write_text('Externally executed check output')
        sdd.progress(self.root, 'SPEC-001', 'TASK-001', 'done', 'evidence.txt')
        sdd.verify(self.root, 'SPEC-001', {'requirements': [
            {'id': 'REQ-001', 'command': 'external-check', 'result': 'failed', 'evidence': 'evidence.txt'}]})
        self.assertTrue(callable(getattr(sdd, 'validate_completion', None)))
        self.assertTrue(sdd.validate_completion(self.root, 'SPEC-001'))
        sdd.verify(self.root, 'SPEC-001', {'requirements': [
            {'id': 'REQ-001', 'command': 'external-check', 'result': 'passed', 'evidence': 'evidence.txt'}]})
        self.assertEqual([], sdd.validate_completion(self.root, 'SPEC-001'))

    def test_malformed_state_returns_controlled_cli_error(self):
        path = self.ready()
        data = json.loads(path.read_text()); data['approvals'] = []
        path.write_text(json.dumps(data))
        self.assertEqual(2, sdd.main(['status', '--root', str(self.root), '--id', 'SPEC-001']))

    def test_odd_is_default_and_unknown_methodology_rejected(self):
        raw = json.loads((ROOT / 'examples/next-react/answers.json').read_text())
        self.assertEqual('odd', install.validated(raw, self.root).get('methodology'))
        with self.assertRaises(ValueError):
            install.validated({**raw, 'methodology': 'unknown'}, self.root)

    def test_install_localizes_sdd_and_preserves_custom_gate_on_upgrade(self):
        for lang in ('en', 'es'):
            with self.subTest(lang=lang), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                raw = json.loads((ROOT / 'examples/next-react/answers.json').read_text())
                install.install(root, install.validated(raw, root), {'modules': []}, docs_lang=lang)
                manifest = root / 'harness.json'
                old = json.loads(manifest.read_text())
                old['checks'].append({'name': 'team:custom', 'command': ['echo', 'custom'], 'required': False})
                manifest.write_text(json.dumps(old))
                profile = install.validated({**raw, 'methodology': 'sdd'}, root)
                install.install(root, profile, {'modules': []}, docs_lang=lang)
                self.assertTrue((root / 'aikya/scripts/harness/sdd_engine.py').is_file())
                self.assertTrue((root / 'aikya/docs/specs/README.md').is_file())
                names = [c['name'] for c in json.loads(manifest.read_text())['checks']]
                self.assertEqual(1, names.count('sdd:traceability'))
                self.assertIn('team:custom', names)
                install.install(root, profile, {'modules': []}, docs_lang=lang)
                self.assertEqual(names, [c['name'] for c in json.loads(manifest.read_text())['checks']])

    def test_registry_keeps_develop_commands_and_new_sdd_commands(self):
        for name in ('aikya-analyze', 'aikya-models', 'aikya-tokens', 'aikya-specify', 'aikya-implement'):
            self.assertIn(name, aikya_setup.BOOTSTRAP_COMMANDS)

class SddAdoptionTests(unittest.TestCase):
    def test_analyze_explicit_opt_in_and_refresh_preserve_methodology(self):
        from aikya.discovery.analyze import execute
        import inspect
        self.assertIn('methodology', inspect.signature(execute).parameters)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'pom.xml').write_text('<project/>')
            preview = execute(root, dry_run=True, methodology='sdd', docs_lang='en')
            self.assertFalse(preview['writes'])
            paths = {p['path'] for p in preview['plan']}
            self.assertIn('aikya/scripts/harness/sdd_engine.py', paths)
            self.assertIn('aikya/docs/specs/README.md', paths)
            self.assertFalse((root / '.harness').exists())
            result = execute(root, approved=True, methodology='sdd', docs_lang='en')
            self.assertEqual('READY', result['status'])
            profile = json.loads((root / '.harness/project-profile.json').read_text())
            self.assertEqual('sdd', profile['decisions']['methodology'])
            (root / 'pom.xml').write_text('<project>updated</project>')
            execute(root, refresh=True, approved=True, docs_lang='en')
            self.assertEqual('sdd', json.loads((root / '.harness/project-profile.json').read_text())['decisions']['methodology'])

    def test_analyze_can_upgrade_owned_standard_profile_without_losing_decisions(self):
        from aikya.discovery.analyze import execute
        import inspect
        self.assertIn('methodology', inspect.signature(execute).parameters)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root / 'pom.xml').write_text('<project/>')
            execute(root, approved=True, docs_lang='en',methodology='odd')
            p = root / '.harness/project-profile.json'
            old = json.loads(p.read_text()); old['decisions']['notes'] = 'Team convention'
            p.write_text(json.dumps(old))
            preview = execute(root, dry_run=True, methodology='sdd', docs_lang='en')
            self.assertIn('.harness/backup-v611/harness.json', {o['path'] for o in preview['plan']})
            execute(root, approved=True, methodology='sdd', docs_lang='en')
            current = json.loads(p.read_text())['decisions']
            self.assertEqual('sdd', current['methodology'])
            self.assertEqual('Team convention', current['notes'])

    def test_customized_sdd_gate_blocks_before_other_writes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); p = root / 'harness.json'
            p.write_text(json.dumps({'schema_version': 2, 'checks': [
                {'name':'sdd:traceability','command':['echo','unsafe'],'required':False}]}))
            old = p.read_bytes()
            raw = json.loads((ROOT / 'examples/next-react/answers.json').read_text())
            raw['methodology'] = 'sdd'
            with self.assertRaises(ValueError):
                install.install(root, install.validated(raw, root), {'modules': []})
            self.assertEqual(old, p.read_bytes())
            self.assertFalse((root / '.harness/project-profile.json').exists())

class SddUpgradeTests(unittest.TestCase):
    def test_standard_to_sdd_upgrades_known_generator_and_preserves_backup(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw = json.loads((ROOT/'examples/next-react/answers.json').read_text())
            install.install(root, install.validated(raw, root), {'modules': []})
            path = root/'aikya/scripts/harness/scaffold.py'
            # Exact legacy managed asset, retained as a fixture from the pre-SDD baseline.
            old = (ROOT/'tests/fixtures/sdd-upgrade/scaffold.py.txt').read_text()
            path.write_text(old)
            profile = install.validated({**raw, 'methodology':'sdd'}, root)
            install.install(root, profile, {'modules': []})
            self.assertNotEqual(old, path.read_text())
            self.assertEqual(old, (root/'.harness/backup-v611/aikya/scripts/harness/scaffold.py').read_text())

    def test_sdd_upgrade_stops_for_custom_generator_without_touching_it(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw = json.loads((ROOT/'examples/next-react/answers.json').read_text())
            install.install(root, install.validated(raw, root), {'modules': []})
            path = root/'aikya/scripts/harness/scaffold.py'
            path.write_text('# team-specific generator\n')
            before = (root/'.harness/project-profile.json').read_bytes()
            with self.assertRaises(ValueError):
                install.install(root, install.validated({**raw, 'methodology':'sdd'}, root), {'modules': []})
            self.assertEqual('# team-specific generator\n', path.read_text())
            self.assertEqual(before, (root/'.harness/project-profile.json').read_bytes())

class SddLanguageAndExecutionTests(unittest.TestCase):
    def test_spec_documents_follow_spanish_policy_without_translating_state(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw = json.loads((ROOT/'examples/next-react/answers.json').read_text())
            install.install(root, install.validated({**raw,'methodology':'sdd'}, root), {'modules':[]}, docs_lang='es')
            spec = json.loads((ROOT/'examples/sdd/development/order-api/spec.json').read_text())
            sdd.initialize(root, spec)
            folder = root/'aikya/docs/specs/development/SPEC-001'
            self.assertIn('## Objetivo', (folder/'spec.md').read_text())
            self.assertFalse((folder/'verification.md').exists())
            self.assertIsNone(json.loads((folder/'state.json').read_text())['verification'])
            self.assertEqual('development', json.loads((folder/'state.json').read_text())['kind'])

    def test_global_runtime_can_register_and_run_sdd_without_source_imports(self):
        with tempfile.TemporaryDirectory() as d:
            import subprocess
            base = Path(d); home=base/'home'; project=base/'project'
            aikya_setup.setup(ROOT, project, 'global', home=home)
            runtime=home/'.claude/aikya-harnes'
            project.mkdir()
            result=subprocess.run([sys.executable,'-B',str(runtime/'sdd_engine.py'),'lint','--root',str(project)],capture_output=True,text=True,cwd=base)
            self.assertEqual(0,result.returncode,result.stderr)
            self.assertTrue(json.loads(result.stdout)['valid'])

    def test_denied_infrastructure_mutation_writes_no_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            raw=json.loads((ROOT/'examples/infra-terraform-only/answers.json').read_text())
            profile=install.validated({**raw,'methodology':'sdd'},root)
            infra=module('sdd_deny_infra','template/scripts/harness/infrastructure.py')
            code,_=infra.generate(root,profile,approved=True,spec_id='SPEC-002',task_id='TASK-001')
            self.assertEqual(2,code)
            self.assertFalse((root/'infra').exists())

class SddManifestSafetyTests(unittest.TestCase):
    def test_dangling_quality_manifest_symlink_is_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'project';root.mkdir()
            outside=Path(d)/'outside.json'
            (root/'harness.json').symlink_to(outside)
            raw=json.loads((ROOT/'examples/next-react/answers.json').read_text())
            with self.assertRaises(ValueError):
                install.install(root,install.validated({**raw,'methodology':'sdd'},root),{'modules':[]})
            self.assertFalse(outside.exists())
            self.assertFalse((root/'.harness/project-profile.json').exists())

class SddInstalledUpgradeTests(unittest.TestCase):
    def test_spanish_upgrade_engine_does_not_depend_on_replaced_locale_helpers(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            raw=json.loads((ROOT/'examples/next-react/answers.json').read_text())
            install.install(root,install.validated(raw,root),{'modules':[]},docs_lang='es')
            helper=root/'aikya/scripts/harness/docs_templates_es.py'
            previous='def pages(profile, modules): return {}\n'
            helper.write_text(previous)
            install.install(root,install.validated({**raw,'methodology':'sdd'},root),{'modules':[]},docs_lang='es')
            self.assertEqual(previous,helper.read_text())
            result=subprocess.run([sys.executable,'-B',str(root/'aikya/scripts/harness/sdd_engine.py'),'new','--root',str(root),'--input',str(ROOT/'examples/sdd/development/order-api/spec.json')],capture_output=True,text=True,cwd=root)
            self.assertEqual(0,result.returncode,result.stderr)
            self.assertIn('## Objetivo',(root/'aikya/docs/specs/development/SPEC-001/spec.md').read_text())

class SddMissingStateTests(unittest.TestCase):
    def test_lint_rejects_spec_directory_with_missing_state(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            folder=root/'aikya/docs/specs/development/SPEC-001';folder.mkdir(parents=True)
            (folder/'spec.md').write_text('# A previously recorded specification\n')
            self.assertFalse(sdd.validate(root)['valid'])

    def test_lint_rejects_dangling_spec_base_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'aikya/docs').mkdir(parents=True)
            (root/'aikya/docs/specs').symlink_to(root/'missing')
            self.assertFalse(sdd.validate(root)['valid'])


if __name__ == '__main__':
    unittest.main()
