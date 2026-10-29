#!/usr/bin/env python3
"""Offline executable contracts for every public Claude command.

This does not invoke a model, install third-party skills, fetch dependencies or
apply infrastructure. Evidence is produced in disposable controlled projects.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from aikya.installation import registration as aikya_setup
from aikya.cli.commands import BOOTSTRAP_COMMANDS
from aikya.documentation.layout import validate_layout, validate_generated_document_paths


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Battery:
    def __init__(self, base):
        self.base = base
        self.projects = {}
        self.results = {name: {'checks': [], 'markdown_changes': []} for name in BOOTSTRAP_COMMANDS}
        self.env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': '',
                    'AIKYA_EXECUTION_CACHE': str(base / 'execution-cache')}
        self.unrelated = base / 'unrelated'
        self.unrelated.mkdir()

    def snapshot(self):
        return {name + '/' + p.relative_to(root).as_posix(): sha(p.read_bytes())
                for name, root in self.projects.items() for p in root.rglob('*.md') if p.is_file()}

    def run(self, command, script, arguments=(), *, expected=0, contains=None, cwd=None):
        before = self.snapshot()
        entry = list(script) if isinstance(script, tuple) else [str(script)]
        argv = [sys.executable, '-B', *entry, *map(str, arguments)]
        started = time.monotonic()
        result = subprocess.run(argv, cwd=cwd or self.unrelated, env=self.env,
                                capture_output=True, text=True, timeout=90)
        output = result.stdout + result.stderr
        if result.returncode != expected or (contains and contains.lower() not in output.lower()):
            raise AssertionError(command + ': ' + repr(argv) + '\n' + output[-6000:])
        after = self.snapshot()
        changes = sorted(key for key, digest in after.items() if before.get(key) != digest)
        row = self.results[command]
        row['checks'].append({'support': (' '.join(script) if isinstance(script, tuple) else Path(script).name), 'arguments': [str(a).replace(str(ROOT), '<source>').replace(str(self.base), '<fixture>') for a in arguments],
                              'exit': result.returncode, 'expected_exit': expected, 'output_sha256': sha(output.encode()),
                              'asserted_output': contains, 'stdout_bytes': len(result.stdout.encode('utf8')),
                              'stderr_bytes': len(result.stderr.encode('utf8')), 'duration_seconds': round(time.monotonic()-started, 6),
                              'model': None, 'tokens': None, 'mode': 'offline_backend_contract'})
        row['markdown_changes'] = sorted(set(row['markdown_changes']) | set(changes))
        return result.stdout

    def fixture(self, name, value):
        path = self.base / (name + '.json')
        path.write_text(json.dumps(value))
        return path

    def helper(self, project, name):
        return self.projects[project] / 'aikya/scripts/harness' / name

    def onboarding(self):
        cli = ('-m', 'aikya')
        for name, method, example in [('odd', 'odd', 'next-react'), ('sdd', 'sdd', 'next-react'),
                                       ('mobile', 'odd', 'native-kotlin-ios'), ('infra', 'odd', 'infra-terraform-only')]:
            # Fixture aliases are selected from real versioned interview inputs.
            if example == 'native-kotlin-ios':
                example = 'mobile-native-kotlin-swift'
            root = self.base / name
            root.mkdir()
            self.projects[name] = root
            answers = ROOT / 'examples' / example / 'answers.json'
            if not answers.is_file() and name == 'mobile':
                candidates = sorted((ROOT / 'examples').glob('*/answers.json'))
                answers = next(p for p in candidates if json.loads(p.read_text()).get('mobile', 'none') != 'none')
            self.run('aikya-init', cli, ['init', '--target', root, '--answers', answers, '--methodology', method, '--docs-lang', 'en', '--external', 'skip'])
        odd = self.projects['odd']; sdd = self.projects['sdd']; infra = self.projects['infra']
        self.run('aikya-init', cli, ['init', '--target', odd, '--answers', self.fixture('existing-answers', {'mode': 'existing'}), '--methodology', 'odd'], expected=2, contains='only for new projects')
        existing = self.base / 'existing'; existing.mkdir(); (existing / 'pom.xml').write_text('<project/>')
        self.projects['existing'] = existing
        self.run('aikya-analyze', cli, ['analyze', '--target', existing, '--approved', '--methodology', 'sdd', '--docs-lang', 'es'])
        self.run('aikya-answers', cli, ['answers', '--target', self.base / 'answers-preview', '--answers', ROOT / 'examples/next-react/answers.json', '--methodology', 'odd', '--dry-run'])
        self.run('aikya-doctor', cli, ['requirements', '--target', odd, '--answers', ROOT / 'examples/next-react/answers.json'])
        self.run('aikya-project', self.helper('odd', 'scaffold.py'), ['plan'])
        self.run('aikya-scaffold', self.helper('odd', 'scaffold.py'), ['plan'])
        self.run('aikya-infra', self.helper('infra', 'infrastructure.py'), ['plan', '--target', infra])
        self.run('aikya-infra', self.helper('infra', 'infrastructure.py'), ['generate', '--target', infra], expected=2, contains='Aprobación')
    def exercise(self):
        self.onboarding()
        odd = self.projects['odd']; sdd = self.projects['sdd']; infra = self.projects['infra']
        workflow = self.helper('odd', 'documentation_workflows.py')
        self.run('aikya-memory', ('-m', 'aikya'), ['memory', '--target', odd, '--dry-run'], contains='preview')
        self.run('aikya-memory', ('-m', 'aikya'), ['memory', '--target', odd, '--refresh'], contains='html_path')
        self.run('aikya-memory', ('-m', 'aikya'), ['memory', '--target', odd, '--dry-run', '--watch'], expected=2, contains='cannot')
        feature = self.fixture('feature', {'title': 'Controlled lookup', 'objective': 'Return a stable controlled missing-item response.',
                                           'acceptance': ['An absent controlled ID returns the specified response.']})
        for command, project in [('aikya-feature', 'odd'), ('aikya-mobile-feature', 'mobile')]:
            root = self.projects[project]; script = self.helper(project, 'documentation_workflows.py')
            self.run(command, script, ['write', '--root', root, '--command', command, '--slug', 'lookup', '--input', feature], expected=2, contains='approval')
            self.run(command, script, ['write', '--root', root, '--command', command, '--slug', 'lookup', '--input', feature, '--approved'])
        bug = self.fixture('bug', {'id': 'BUG-001', 'title': 'Controlled missing-item failure', 'sections': {
            'summary': 'Controlled lookup raises.', 'environment': 'Disposable synthetic fixture.',
            'steps-to-reproduce': '1. Query the absent controlled ID.', 'expected-result': 'A documented missing-item response.',
            'actual-result': 'A controlled exception.'}})
        library = self.helper('odd', 'documentation_templates.py')
        bug_args = ['write', '--root', odd, '--template', 'general-swe/foundations/bug-report', '--input', bug, '--approved']
        self.run('aikya-bugfix', library, bug_args)
        self.run('aikya-bugfix', library, bug_args, expected=2, contains='already exists')
        self.run('aikya-arc-review', workflow, ['plan', '--root', odd, '--command', 'aikya-arc-review'], contains='read_only')
        self.run('aikya-skills-status', self.helper('odd', 'external_skills.py'), ['status', '--target', odd])
        self.run('aikya-skills-plan', self.helper('odd', 'external_skills.py'), ['plan', '--target', odd])
        self.run('aikya-install-skill', self.helper('odd', 'external_skills.py'), ['install', '--target', odd, '--record-comparison'], expected=2, contains='approval')
        if (odd / 'aikya/docs/tools/skill-comparison.md').exists():
            raise AssertionError('Denied installation created a comparison report')
        self.run('aikya-quality', self.helper('odd', 'skills_lint.py'))
        # Execute real local check subprocesses and ensure failures are not passed.
        config = odd / 'harness.json'
        original = config.read_bytes()
        try:
            checks = {'checks': [{'name': 'controlled-unit', 'required': True, 'command': [sys.executable, '-c', 'assert 2 + 2 == 4']},
                                 {'name': 'controlled-security', 'required': True, 'command': [sys.executable, '-c', 'assert True']}]}
            config.write_text(json.dumps(checks))
            self.run('aikya-tests', self.helper('odd', 'run_checks.py'), contains='PASSED')
            checks['checks'][0]['command'] = [sys.executable, '-c', 'raise SystemExit(7)']
            config.write_text(json.dumps(checks))
            self.run('aikya-tests', self.helper('odd', 'run_checks.py'), expected=1, contains='exit 7')
            checks['checks'][0]['command'] = None
            config.write_text(json.dumps(checks))
            self.run('aikya-verify', self.helper('odd', 'run_checks.py'), expected=1, contains='NOT_CONFIGURED')
        finally:
            config.write_bytes(original)
        text = self.base / 'observed.md'; text.write_text('# Controlled observation\n\nThe fixture check exits with the expected result.\n')
        layout = self.helper('odd', 'docs_layout.py')
        self.run('aikya-docs', layout, ['write', '--root', odd, '--path', 'plan/acceptance.md', '--input', text], expected=2, contains='--approved')
        self.run('aikya-docs', layout, ['write', '--root', odd, '--path', 'plan/acceptance.md', '--input', text, '--approved'])
        self.run('aikya-docs', layout, ['write', '--root', odd, '--path', '../outside.md', '--input', text, '--approved'], expected=2, contains='contained')
        self.run('aikya-docs-sync', layout, ['index', '--root', odd, '--approved'])
        self.run('aikya-verify', self.helper('odd', 'docs_guard.py'), ['base'])
        # Model inspection is deliberately a policy inspection, without a model request.
        code = "import json;from pathlib import Path;from aikya.routing.policy import validated;from aikya.routing.models import capability_status;p=validated(json.loads(Path('" + str(odd / '.aikya/model-policy.json') + "').read_text()));print(json.dumps(capability_status(p, '0.0.0')))"
        inspect = self.base / 'inspect_model.py'
        inspect.write_text("import sys;sys.path.insert(0," + repr(str(ROOT / 'src')) + ");" + code)
        self.run('aikya-models', inspect, contains='ready_for_cli_delegation')
        transcript = self.base / 'controlled.jsonl'
        transcript.write_text(json.dumps({'message': {'role': 'assistant', 'id': 'controlled-1', 'model': 'synthetic-model',
                                                       'usage': {'input_tokens': 10, 'output_tokens': 5}}}) + '\n')
        out = self.run('aikya-tokens', self.helper('odd', 'token_report.py'), ['--path', transcript, '--budget-tokens', 100])
        if json.loads(out)['local_budget']['used_percentage'] != 15:
            raise AssertionError('Controlled usage percentage is incorrect')
        self.run('aikya-tokens', self.helper('odd', 'token_report.py'), expected=2, contains='--path is required')
        engine = self.helper('sdd', 'sdd_engine.py')
        fixture = ROOT / 'examples/sdd/development/order-api'
        self.run('aikya-specify', engine, ['new', '--root', sdd, '--input', fixture / 'spec.json'])
        self.run('aikya-plan', engine, ['plan', '--root', sdd, '--id', 'SPEC-001', '--input', fixture / 'plan.json'], expected=2, contains='Approve')
        self.run('aikya-clarify', engine, ['clarify', '--root', sdd, '--id', 'SPEC-001', '--input', fixture / 'clarify.json'])
        self.run('aikya-clarify', engine, ['approve', '--root', sdd, '--id', 'SPEC-001', '--stage', 'spec', '--actor', 'controlled-reviewer'])
        self.run('aikya-plan', engine, ['plan', '--root', sdd, '--id', 'SPEC-001', '--input', fixture / 'plan.json'])
        self.run('aikya-plan', engine, ['approve', '--root', sdd, '--id', 'SPEC-001', '--stage', 'plan', '--actor', 'controlled-reviewer'])
        self.run('aikya-tasks', engine, ['tasks', '--root', sdd, '--id', 'SPEC-001', '--input', fixture / 'tasks.json'])
        self.run('aikya-implement', engine, ['authorize', '--root', sdd, '--id', 'SPEC-001', '--task', 'TASK-001'], expected=2, contains='approved')
        self.run('aikya-tasks', engine, ['approve', '--root', sdd, '--id', 'SPEC-001', '--stage', 'tasks', '--actor', 'controlled-reviewer'])
        self.run('aikya-implement', engine, ['authorize', '--root', sdd, '--id', 'SPEC-001', '--task', 'TASK-001'])
        self.run('aikya-implement', engine, ['progress', '--root', sdd, '--id', 'SPEC-001', '--task', 'TASK-001', '--result', 'done', '--evidence', '../missing.log'], expected=2, contains='Path')
        self.run('aikya-sdd-status', engine, ['status', '--root', sdd, '--id', 'SPEC-001'])
        self.run('aikya-sdd-status', engine, ['lint', '--root', sdd], contains='true')
        self.run('aikya-sdd-status', engine, ['completion', '--root', sdd, '--id', 'SPEC-001'], expected=1, contains='false')
        self.run('aikya-sdd-status', self.helper('odd', 'aikya_cli.py'), ['implement', '--target', odd], expected=2)
        return self.audit()

    def audit(self):
        inventories = {}
        for name, root in self.projects.items():
            errors = validate_layout(root)
            living = sorted(p.relative_to(root).as_posix() for p in (root / 'aikya/docs').rglob('*.md'))
            all_markdown = sorted(p.relative_to(root).as_posix() for p in root.rglob('*.md'))
            errors += validate_generated_document_paths(root, all_markdown)
            for outside in ('docs', 'plans', 'plan', 'features', 'bugs'):
                if (root / outside).exists():
                    errors.append('Unexpected root record directory: ' + outside)
            if errors:
                raise AssertionError(name + ': ' + repr(errors))
            inventories[name] = {'living_markdown': living,
                                 'other_markdown': sorted(p.relative_to(root).as_posix() for p in root.rglob('*.md')
                                                          if not p.is_relative_to(root / 'aikya/docs'))}
        if any(not row['checks'] for row in self.results.values()):
            raise AssertionError('Unexercised public command')
        return {'schema': 1, 'mode': 'offline executable command contracts', 'live_model_execution': False,
                'third_party_installation': False, 'infrastructure_deployment': False,
                'commands': self.results, 'command_count': len(self.results),
                'process_checks': sum(len(row['checks']) for row in self.results.values()),
                'projects': inventories, 'valid': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='aikya-commands-') as temporary:
        result = Battery(Path(temporary)).exercise()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'valid': result['valid'], 'commands': result['command_count'], 'process_checks': result['process_checks']}))


if __name__ == '__main__':
    main()
