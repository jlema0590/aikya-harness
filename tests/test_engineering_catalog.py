"""Curated engineering library, provenance and explicit user exclusions."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aikya.catalogs import engineering as catalog
from aikya.installation import facade as install
from aikya.installation import registration as aikya_setup

EXCLUDED = {'digital-law-coordinator','ecommerce-platform-lawyer',
            'legal-quality-reviewer','privacy-dpa-lawyer','saas-contract-lawyer',
            'software-ip-lawyer','ecommerce-platform-terms','legal-research-es-eu',
            'legal-risk-matrix','privacy-data-processing','saas-contract-review',
            'software-ip-licensing'}


class EngineeringCatalogTests(unittest.TestCase):
    def test_only_engineering_components_packaged(self):
        self.assertEqual(27,len(catalog.AGENTS - {'log-summarizer', 'aikya-auxiliary-analyzer', 'aikya-docs-assistant'}))
        self.assertTrue({'log-summarizer','aikya-auxiliary-analyzer','aikya-docs-assistant'} <= catalog.AGENTS)
        self.assertEqual(29,len(catalog.SKILLS))
        self.assertFalse((catalog.AGENTS|catalog.SKILLS)&EXCLUDED)
        self.assertNotIn('security-reviewer', catalog.AGENTS)
        for path in (ROOT/'src/aikya/resources/engineering').rglob('*.md'):
            text=path.read_text(encoding='utf8').lower()
            for bad in ('linkedin','derecho digital','propiedad intelectual','saas contract'):
                self.assertNotIn(bad,text,path)
        self.assertFalse((ROOT/'src/aikya/resources/engineering/agents/security-reviewer.md').exists())

    def test_core_and_stack_selection(self):
        base={'ci':'none','deployment':'none','architecture':'layered','backend':'java',
              'frontend':'react','mobile':'none'}
        items=catalog.discover(ROOT,base,[])
        self.assertNotIn('nextjs-developer',items['agents'])
        self.assertNotIn('flutter-architecture',items['skills'])
        self.assertIn('testing-strategy',items['skills'])
        full={**base,'backend':'next','frontend':'react','ci':'github-actions','deployment':'kubernetes'}
        actual=catalog.discover(ROOT,full,[{'technology':'next'},{'technology':'react'}])
        for item in ('nextjs-developer','cicd-engineer','docker-developer','cloud-architect','orchestrator'):
            self.assertIn(item,actual['agents'])
        for item in ('nextjs-architecture','kubernetes-operations','cicd-pipelines'):
            self.assertIn(item,actual['skills'])

    def test_project_setup_includes_catalog_and_global_does_not_mutate_projects(self):
        with tempfile.TemporaryDirectory() as temp:
            project=Path(temp)/'new';home=Path(temp)/'home';home.mkdir()
            logs=aikya_setup.setup(ROOT,project,'global',home=home)
            self.assertTrue((home/'.claude/aikya-harnes/engineering_catalog.py').exists())
            self.assertTrue((home/'.claude/aikya-harnes/engineering/skills/vue-architecture/SKILL.md').exists())
            self.assertFalse(project.exists())
            self.assertTrue(any('global' in x for x in logs))

    def test_install_initializes_selected_agents_skills_and_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            data=json.loads((ROOT/'examples/new-next-react.json').read_text())
            profile=install.validated(data,root)
            install.install(root,profile,{'modules':[]})
            self.assertTrue((root/'.claude/agents/nextjs-developer.md').exists())
            self.assertTrue((root/'.claude/skills/nextjs-architecture/SKILL.md').exists())
            self.assertFalse((root/'.claude/agents/flutter-developer.md').exists())
            self.assertFalse((root/'.claude/skills/flutter-architecture/SKILL.md').exists())
            self.assertTrue((root/'.claude/agents/security-reviewer.md').exists())
            for name in ('aikya/docs/tools/agents.md','aikya/docs/skills.md','.harness/engineering-catalog.json'):
                self.assertTrue((root/name).is_file(),name)
            doc=(root/'aikya/docs/skills.md').read_text()
            self.assertIn('Aikya Engineering',doc)
            self.assertTrue((root/'aikya/scripts/harness/engineering_catalog.py').exists())
            self.assertTrue((root/'aikya/scripts/harness/engineering/skills/terraform-iac/SKILL.md').exists())
            check=subprocess.run([sys.executable,str(root/'aikya/scripts/harness/engineering_catalog.py'),'plan','--root',str(root), '--names','terraform-iac'],capture_output=True,text=True)
            self.assertEqual(0,check.returncode,check.stderr)
            self.assertIn('terraform-iac',check.stdout)
            reject=subprocess.run([sys.executable,str(root/'aikya/scripts/harness/engineering_catalog.py'),'install','--root',str(root),'--names','terraform-iac'],capture_output=True,text=True)
            self.assertNotEqual(0,reject.returncode)
            self.assertFalse((root/'.claude/skills/terraform-iac').exists())
            enabled=subprocess.run([sys.executable,str(root/'aikya/scripts/harness/engineering_catalog.py'),'install','--root',str(root),'--names','terraform-iac', '--approved'],capture_output=True,text=True)
            self.assertEqual(0,enabled.returncode,enabled.stderr)
            self.assertTrue((root/'.claude/skills/terraform-iac/SKILL.md').exists())
            self.assertIn('terraform-iac',(root/'aikya/docs/skills.md').read_text())

    def test_repeat_install_preserves_personalized_specialist_and_docs(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            profile={'backend':'node','frontend':'none','mobile':'none'}
            choices=catalog.discover(root,profile)
            catalog.install_selected(root,choices)
            path=root/'.claude/agents/node-backend-developer.md'
            path.write_text(path.read_text()+'\n# personalizado\n')
            docs=root/'aikya/docs/tools/agents.md';docs.write_text('custom team doc\n')
            logs=catalog.install_selected(root,choices)
            self.assertIn('# personalizado',path.read_text())
            self.assertEqual('custom team doc\n',docs.read_text())
            self.assertTrue(any('CONSERVADO personalizado' in x for x in logs))

    def test_reject_unapproved_or_ineligible(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in EXCLUDED|{'linkedIn', '../attack'}:
                with self.subTest(name=name),self.assertRaises(ValueError):
                    catalog.install_selected(root,{'agents':[name], 'skills':[]})
            self.assertFalse((root/'.claude').exists())

if __name__=='__main__': unittest.main()
