"""Pruebas v4: integración sin red, consentimiento, diseño UI y especificación Agent Skills."""
import runtime_support
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from aikya.catalogs import external as ext
from aikya.installation import facade as installer


def load_module(path: Path,name: str):
    spec=runtime_support.module_spec(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module);module=getattr(module,'_module',module)
    return getattr(module, '_module', module)

LINTER=load_module(HERE/'src/aikya/resources/project_template/scripts/harness/skills_lint.py','harness_v4_linter')


class ExternalIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        (self.root/'.claude/skills').mkdir(parents=True)
        self.profile={'frontend':'none','mobile':'none','backend':'java'}
    def tearDown(self):
        self.temp.cleanup()

    def test_backend_has_no_ui_skill(self):
        self.assertEqual(ext.enabled_names(self.profile),['ponytail','graphify'])
        self.assertNotIn('ui-ux-pro-max-cli',' '.join(ext.planned_commands(self.profile)))
        self.profile['frontend']='vue'
        self.assertIn('ui-ux-pro-max',ext.enabled_names(self.profile))
        self.assertIn('ui-ux-pro-max-cli',' '.join(ext.planned_commands(self.profile)))

    def test_official_sources_and_double_y_package(self):
        self.assertEqual(ext.SOURCES['ponytail'],'https://github.com/DietrichGebert/ponytail.git')
        self.assertEqual(ext.SOURCES['graphify'],'https://github.com/Graphify-Labs/graphify.git')
        self.assertEqual(ext.SOURCES['ui-ux-pro-max'],'https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git')
        self.assertIn('graphifyy',' '.join(ext.planned_commands(self.profile)))

    def test_explicit_consent_required_no_external_commands(self):
        with self.assertRaises(PermissionError):
            ext.install_all(self.root,self.profile,permission=False)
        self.assertFalse((self.root/'.harness/external-skills-lock.json').exists())
        self.assertTrue(ext.install_all(self.root,self.profile,permission=False,dry_run=True)['dry_run'])
        self.assertFalse((self.root/'.harness').exists())

    def test_safe_copy_preserves_user_and_rejects_symlink(self):
        src=self.root/'source'; src.mkdir()
        (src/'SKILL.md').write_text('---\nname: ponytail\ndescription: Example\n---\nTask\n')
        dest=self.root/'.claude/skills/ponytail'
        ext._copy_safe_skill(src,dest)
        self.assertTrue((dest/'SKILL.md').exists())
        with self.assertRaises(FileExistsError):
            ext._copy_safe_skill(src,dest)
        src2=self.root/'source2';src2.mkdir()
        (src2/'SKILL.md').write_text('skill')
        (src2/'unsafe').symlink_to('/etc/passwd')
        with self.assertRaises(ValueError):
            ext._copy_safe_skill(src2,self.root/'.claude/skills/unsafe')

    def test_partial_install_records_failures(self):
        with patch.dict(ext.INSTALLERS,{
            'ponytail':lambda r:{'state':'installed','commit':'1234'},
            'graphify':lambda r:(_ for _ in ()).throw(RuntimeError('offline'))
        }):
            lock=ext.install_all(self.root,self.profile,permission=True)
        self.assertEqual(lock['skills']['ponytail']['state'],'installed')
        self.assertEqual(lock['skills']['graphify']['state'],'failed')
        self.assertTrue((self.root/'.harness/external-skills-lock.json').is_file())
        self.assertEqual(json.loads((self.root/'.harness/external-skills-lock.json').read_text())['skills']['graphify']['detail'],'offline')

    def test_agent_skills_spec_linter_template(self):
        errors=LINTER.validate(HERE/'src/aikya/resources/project_template')
        self.assertEqual(errors,[])
        bad=self.root/'.claude/skills/BadName';bad.mkdir()
        (bad/'SKILL.md').write_text('no frontmatter')
        self.assertTrue(LINTER.validate(self.root))

    def test_install_omits_design_without_actual_decisions(self):
        for front in ('none','react'):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                profile=installer.validated({**json.loads((HERE/'examples/new-next-react.json').read_text()),
                    'backend':'java','backend_framework':'spring-boot','frontend':front,
                    'package_manager':'npm'},root)
                installer.install(root,profile,{'modules':[],'findings':[]})
                design=(root/'aikya/docs/design/design-system.md').exists()
                self.assertFalse(design)
                self.assertTrue((root/'.claude/hooks/skills_ready.py').is_file())
                self.assertTrue((root/'aikya/scripts/harness/external_skills.py').is_file())
                self.assertEqual(subprocess.run([sys.executable,str(root/'aikya/scripts/harness/skills_lint.py')],
                                                cwd=root,capture_output=True).returncode,0)

    def test_upgrade_unmodified_v3_and_preserve_custom_code(self):
        previous=HERE/'tests/fixtures'
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            old=root/'scripts/harness/docs_guard.py'
            old.parent.mkdir(parents=True)
            old.write_bytes((previous/'v3_docs_guard.py').read_bytes())
            custom=root/'.claude/skills/feature/SKILL.md'
            custom.parent.mkdir(parents=True)
            custom.write_text('PERSONALIZADO; no sobrescribir')
            profile=installer.validated({'name':'upgrade','backend':'java',
                'backend_framework':'spring-boot','frontend':'react','mode':'existing'},root)
            actions=installer.install(root,profile,{'modules':[],'findings':[]})
            self.assertFalse(any('ACTUALIZADO DESDE v3' in x for x in actions))
            self.assertEqual(old.read_bytes(),(previous/'v3_docs_guard.py').read_bytes())
            self.assertEqual((root/'aikya/scripts/harness/docs_guard.py').read_bytes(),(HERE/'src/aikya/resources/project_template/scripts/harness/docs_guard.py').read_bytes())
            self.assertFalse((root/'.harness/backup-v3/aikya/scripts/harness/docs_guard.py').exists())
            self.assertEqual(custom.read_text(),'PERSONALIZADO; no sobrescribir')
            self.assertTrue((root/'.claude/rules/02-context-budget.md').is_file())

    def test_ui_docs_guard_requires_design_system_for_ui_changes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            profile=installer.validated({'name':'design','backend':'none',
                'frontend':'vue','mode':'new'},root)
            installer.install(root,profile,{'modules':[],'findings':[]})
            guard=load_module(root/'aikya/scripts/harness/docs_guard.py','guard_ui_case')
            requested=guard.affected_docs('feature',['apps/web/src/components/Button.vue'])
            self.assertIn('aikya/docs/design/design-system.md',requested)
            not_ui=guard.affected_docs('bug',['apps/api/server.ts'])
            self.assertNotIn('aikya/docs/design/design-system.md',not_ui)

    def test_cli_with_answers_plan_does_not_download(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'new'
            result=subprocess.run([sys.executable,str(HERE / 'src/aikya/installation/facade.py'),
                '--target',str(root),'--answers',str(HERE/'examples/new-next-react.json'),
                '--external','plan'],text=True,capture_output=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('Skills externas PENDIENTES',result.stdout)
            self.assertFalse((root/'.harness/external-skills-lock.json').exists())
            self.assertTrue((root/'.claude/skills/feature/SKILL.md').is_file())

if __name__=='__main__':
    unittest.main()
