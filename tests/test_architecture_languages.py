"""New engineering specialists, stack-independent architecture and example profiles."""
from __future__ import annotations
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aikya.catalogs import engineering as catalog
from aikya.installation import facade as install

LANGUAGES={
    'java': ('java-developer','java-engineering'),
    'dotnet': ('dotnet-developer','dotnet-engineering'),
    'python': ('python-developer','python-engineering'),
    'react': ('react-developer','react-engineering'),
    'angular': ('angular-developer','angular-engineering'),
}
ARCHITECTURES={
    'clean': ('clean-architecture-architect','clean-architecture'),
    'layered': ('layered-architecture-architect','layered-architecture'),
    'modular-monolith': ('monolith-architect','modular-monolith-architecture'),
    'microservices': ('microservices-architect','microservices-architecture'),
}

class SpecialistIntegrationTests(unittest.TestCase):
    def test_catalog_has_expected_names_and_disallows_prohibited_material(self):
        self.assertEqual(27, len(catalog.AGENTS - {'log-summarizer','aikya-auxiliary-analyzer','aikya-docs-assistant'}))
        self.assertEqual(29, len(catalog.SKILLS))
        self.assertEqual(30,len(list((ROOT/'src/aikya/resources/engineering/agents').glob('*.md'))))
        self.assertEqual(29,len(list((ROOT/'src/aikya/resources/engineering/skills').glob('*/SKILL.md'))))
        for entry in (ROOT/'src/aikya/resources/engineering').rglob('*.md'):
            body=entry.read_text(encoding='utf8')
            for prohibited in ('linkedin','derecho digital','propiedad intelectual','saas contract'):
                self.assertNotIn(prohibited,body.lower())
            self.assertTrue(body.startswith('---\n'),entry)
            self.assertRegex(body,r'(?m)^name:\s*[a-z0-9-]+')
            self.assertRegex(body,r'(?m)^description:')
        for agent in (ROOT/'src/aikya/resources/engineering/agents').glob('*.md'):
            body=agent.read_text(encoding='utf8')
            match=re.search(r'(?m)^skills:\n- ([a-z0-9-]+)',body)
            if match:
                self.assertTrue((ROOT/'src/aikya/resources/engineering/skills'/match.group(1)/'SKILL.md').is_file(),agent)

    def test_language_selected_separately_from_architecture(self):
        for tech,(agent,skill) in LANGUAGES.items():
            with self.subTest(stack=tech):
                profile={'backend':tech if tech in ('java','dotnet','python') else 'none',
                         'frontend':tech if tech in ('react','angular') else 'none',
                         'mobile':'none','architecture':'undecided'}
                selected=catalog.discover(ROOT,profile)
                self.assertIn(agent,selected['agents'])
                self.assertIn(skill,selected['skills'])
                self.assertNotIn('microservices-architect',selected['agents'])
                self.assertNotIn('event-driven-architect',selected['agents'])
        for arch,(agent,skill) in ARCHITECTURES.items():
            with self.subTest(arch=arch):
                result=catalog.discover(ROOT,{'backend':'java','architecture':arch})
                self.assertIn(agent,result['agents'])
                self.assertIn(skill,result['skills'])
                self.assertIn('java-developer',result['agents'])
                if arch != 'microservices':
                    self.assertNotIn('microservices-architect',result['agents'])

    def test_event_driven_and_mobile_are_conditional(self):
        base={'backend':'next','frontend':'react','architecture':'layered'}
        selection=catalog.discover(ROOT,base)
        self.assertIn('react-developer',selection['agents'])
        self.assertIn('nextjs-developer',selection['agents'])
        self.assertNotIn('event-driven-architect',selection['agents'])
        enabled=catalog.discover(ROOT,{**base,'architecture_patterns':['event-driven']})
        self.assertIn('event-driven-architect',enabled['agents'])
        self.assertIn('event-driven-architecture',enabled['skills'])
        android=catalog.discover(ROOT,{'backend':'none','frontend':'none','mobile':'android',
                                      'mobile_framework':'native','android_language':'kotlin'})
        self.assertIn('kotlin-developer',android['agents'])
        self.assertIn('kotlin-engineering',android['skills'])

    def test_all_examples_validate_and_describe_claude_workflow(self):
        examples=sorted((ROOT/'examples').glob('*/answers.json'))
        self.assertEqual(14,len(examples))
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)
            for file in examples:
                with self.subTest(name=file.parent.name):
                    data=json.loads(file.read_text(encoding='utf8'))
                    profile=install.validated(data,target)
                    self.assertEqual(data['name'],profile['name'])
                    doc=(file.parent/'README.md').read_text(encoding='utf8')
                    for keyword in ('/aikya-answers','/aikya-doctor','/aikya-skills-status'):
                        self.assertIn(keyword,doc)
                    selected=catalog.discover(target,profile)
                    self.assertIn('planner',selected['agents'])
                    self.assertTrue(selected['skills'])

    def test_invalid_optional_patterns_are_rejected(self):
        data=json.loads((ROOT/'examples/next-react/answers.json').read_text())
        for patterns in (['event-driven','event-driven'],['unknown'], 'event-driven', [42]):
            with self.subTest(patterns=patterns),self.assertRaises(ValueError):
                install.validated({**data,'architecture_patterns':patterns},ROOT)

    def test_conservative_install_and_catalog_manual_activation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            data=json.loads((ROOT/'examples/java-react-clean/answers.json').read_text())
            profile=install.validated(data,root)
            install.install(root,profile,{'modules':[]})
            for name in ('java-developer','react-developer','clean-architecture-architect','event-driven-architect'):
                self.assertTrue((root/'.claude/agents'/f'{name}.md').is_file(),name)
            for name in ('java-engineering','react-engineering','clean-architecture','event-driven-architecture'):
                self.assertTrue((root/'.claude/skills'/name/'SKILL.md').is_file(),name)
            self.assertFalse((root/'.claude/agents/angular-developer.md').exists())
            self.assertTrue((root/'aikya/scripts/harness/engineering/agents/angular-developer.md').exists())
            report=(root/'aikya/docs/tools/agents.md').read_text()
            self.assertIn('java-developer',report)
            source=root/'.claude/agents/java-developer.md'
            source.write_text(source.read_text()+'\n# equipo: personalización\n')
            catalog.install_selected(root,{'agents':['java-developer','angular-developer'],'skills':['angular-engineering']})
            self.assertIn('# equipo: personalización',source.read_text())
            self.assertTrue((root/'.claude/agents/angular-developer.md').exists())
            self.assertIn('angular-engineering',(root/'aikya/docs/skills.md').read_text())

    def test_existing_python_and_angular_project_detection(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'api').mkdir();(root/'web').mkdir()
            (root/'api/pyproject.toml').write_text('[project]\nname="demo"\nversion="0.1.0"\n')
            (root/'web/package.json').write_text('{"dependencies":{"@angular/core":"^20"}}')
            detected=install.detect_project(root)
            modules=detected['modules']
            self.assertTrue(any(m['technology']=='python' for m in modules))
            self.assertTrue(any(m['technology']=='angular' for m in modules))
            selected=catalog.discover(root,{'backend':'python','frontend':'angular','architecture':'existing'},modules)
            self.assertIn('python-developer',selected['agents'])
            self.assertIn('angular-developer',selected['agents'])

if __name__=='__main__':unittest.main()
