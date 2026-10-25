"""Regresiones v5.7: Node, infraestructura selectiva, generación segura y migración."""
import runtime_support
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aikya.installation import requirements as aikya_requirements
from aikya.discovery import infrastructure as infrastructure_profile
from aikya.installation import facade as install
from aikya.catalogs import engineering as engineering_catalog

def load(file,name):
    spec=runtime_support.module_spec(name,file)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module);module=getattr(module,'_module',module)
    return getattr(module, '_module', module)

INFRA=load(ROOT/'src/aikya/resources/project_template/scripts/harness/infrastructure.py','aikya_infra_test')

class V57Tests(unittest.TestCase):
    def profile(self,root,**override):
        defaults={'name':'portal-app','mode':'new','repository_layout':'singlerepo',
                  'backend':'next','backend_framework':'next-app-router','frontend':'react','mobile':'none',
                  'runtime_versions':'Node 25.9.0','package_manager':'npm'}
        return install.validated({**defaults,**override},root)

    def selection(self,**changes):
        defaults={'provider':'aws','iac':'terraform','configuration_management':'ansible',
                  'containers':{'enabled':True,'compose':True},'orchestration':'kubernetes',
                  'deployment_method':'helm','environments':['dev','prod'],
                  'image_repository':'ghcr.io/example/portal:1.0.0','container_port':3000}
        defaults.update(changes)
        return defaults

    def test_node_prefixed_versions_are_not_truncated(self):
        for reported,expected in [('v25.9.0','25.9.0'),('v22.15.0','22.15.0'),('v18.20.8','18.20.8'),
                                  ('v24.0.0','24.0.0'),('v20.19.0','20.19.0')]:
            with self.subTest(reported=reported),patch.object(aikya_requirements.shutil,'which',return_value='/bin/node'),patch.object(aikya_requirements.subprocess,'run',return_value=SimpleNamespace(stdout=reported+'\n',stderr='',returncode=0)):
                actual,error=aikya_requirements.command_version('node')
                self.assertEqual(expected,actual)
                self.assertIsNone(error)

    def test_runtime_node_major_constraint_is_still_enforced(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.profile(Path(d),runtime_versions='Node 22.0.0')
            def version(tool):
                return ('25.9.0',None) if tool=='node' else ('11.0.0',None)
            with patch.object(aikya_requirements,'command_version',side_effect=version):
                report=aikya_requirements.check(p,Path(d))
            node=next(x for x in report['checks'] if x['tool']=='node')
            self.assertEqual('version_mismatch',node['status'])
            self.assertEqual('25.9.0',node['installed'])

    def test_infrastructure_profile_validation(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual('terraform',self.profile(Path(d),infrastructure=self.selection())['infrastructure']['iac'])
            with self.assertRaisesRegex(ValueError,'Kubernetes'):
                self.profile(Path(d),infrastructure=self.selection(orchestration='none'))
            with self.assertRaisesRegex(ValueError,'Docker Compose'):
                self.profile(Path(d),infrastructure=self.selection(containers={'enabled':False,'compose':True},orchestration='none',deployment_method='none'))
            with self.assertRaisesRegex(ValueError,'seguro'):
                self.profile(Path(d),infrastructure=self.selection(environments=['../../prod']))

    def test_legacy_profile_is_compatible(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.profile(Path(d))
            self.assertEqual('none',p['infrastructure']['iac'])
            self.assertEqual('none',p['infrastructure']['deployment_method'])

    def test_tool_selection_only_for_requested_technologies(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.profile(Path(d),infrastructure=self.selection())
            tools=aikya_requirements.required_tools(p)
            for name in ('terraform','ansible','docker','docker-compose','helm','kubectl'):
                self.assertIn(name,tools)
            self.assertNotIn('kustomize',tools)
            other=self.profile(Path(d),infrastructure=self.selection(iac='none',configuration_management='none',
                orchestration='none',deployment_method='none',containers={'enabled':False,'compose':False}))
            self.assertFalse(set(('terraform','ansible','docker','helm','kubectl')) & set(aikya_requirements.required_tools(other)))

    def test_engineering_skills_are_selected_by_infra_profile(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.profile(Path(d),infrastructure=self.selection())
            selection=engineering_catalog.discover(Path(d),p,[])
            for agent in ('terraform-engineer','ansible-engineer','docker-developer','kubernetes-engineer','helm-engineer'):
                self.assertIn(agent,selection['agents'])
            self.assertIn('helm-deployment',selection['skills'])
            self.assertNotIn('kustomize-deployment',selection['skills'])
            q=self.profile(Path(d),infrastructure=self.selection(deployment_method='kustomize'))
            selected=engineering_catalog.discover(Path(d),q,[])
            self.assertIn('kustomize-deployment',selected['skills'])
            self.assertNotIn('helm-deployment',selected['skills'])

    def test_plan_does_not_write_and_requires_approval(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.profile(root,infrastructure=self.selection())
            text=INFRA.plan(root,p)
            self.assertIn('infra/terraform/versions.tf',text)
            self.assertIn('infra/ansible/ansible.cfg',text)
            self.assertIn('infra/helm/charts/',text)
            self.assertFalse((root/'infra').exists())
            status,rows=INFRA.generate(root,p,False)
            self.assertEqual(2,status)
            self.assertFalse((root/'infra').exists())

    def test_generated_infrastructure_preserves_files_and_limits_scripts(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.profile(root,infrastructure=self.selection())
            existing=root/'infra/terraform/versions.tf'
            existing.parent.mkdir(parents=True)
            existing.write_text('USER DEFINED\n')
            status,actions=INFRA.generate(root,p,True)
            self.assertEqual(0,status)
            self.assertEqual('USER DEFINED\n',existing.read_text())
            self.assertTrue((root/'infra/ansible/playbooks/site.yml').exists())
            self.assertTrue(any('CONSERVADO infra/terraform/versions.tf' in x for x in actions))
            self.assertTrue(any('PENDIENTE' in x for x in actions))
            self.assertFalse((root/'infra/helm/charts/portal-app/templates/deployment.yaml').is_symlink())

    def test_single_repo_dockerfile_from_real_node_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.profile(root,infrastructure=self.selection(orchestration='none',deployment_method='none'))
            (root/'package.json').write_text(json.dumps({'name':'portal','scripts':{'build':'next build','start':'next start'}}))
            (root/'package-lock.json').write_text('{"name":"portal","lockfileVersion":3,"packages":{}}')
            (root/'.nvmrc').write_text('25.9.0\n')
            files,pending=INFRA.specs(root,p)
            self.assertIn('Dockerfile',files)
            self.assertIn('node:25-bookworm-slim',files['Dockerfile'] if 'node:25-bookworm-slim' in files['Dockerfile'] else files['Dockerfile'].replace('${NODE_VERSION}','25'))
            self.assertIn('compose.apps.yaml',files)
            self.assertNotIn('apps/README.md',files)

    def test_missing_manifest_never_generates_fictional_dockerfile(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.profile(root,infrastructure=self.selection())
            files,pending=INFRA.specs(root,p)
            self.assertNotIn('Dockerfile',files)
            self.assertTrue(any('manifiesto' in x for x in pending))

    def test_yaml_and_kustomize_are_alternatives_to_helm(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for method in ('helm','yaml','kustomize'):
                p=self.profile(root,infrastructure=self.selection(deployment_method=method))
                files,_=INFRA.specs(root,p)
                self.assertEqual(method=='helm',any(x.endswith('/Chart.yaml') for x in files))
                self.assertEqual(method=='kustomize',any(x.endswith('/kustomization.yaml') for x in files))
                self.assertEqual(method in ('yaml','kustomize'),'infra/kubernetes/base/deployment.yaml' in files)

    def test_install_writes_plan_not_remote_infrastructure(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            p=self.profile(root,infrastructure=self.selection())
            install.install(root,p,{'modules':[],'findings':[]})
            self.assertTrue((root/'aikya/docs/infrastructure/plan.md').is_file())
            self.assertTrue((root/'aikya/scripts/harness/infrastructure.py').is_file())
            self.assertTrue((root/'aikya/scripts/harness/infrastructure_profile.py').is_file())
            self.assertFalse((root/'infra/terraform/versions.tf').exists())
            self.assertFalse((root/'infra/ansible/playbooks/site.yml').exists())
            self.assertIn('infra:static',str(json.loads((root/'harness.json').read_text())['checks']))

    def test_installer_migrates_exact_v56_parser_and_preserves_customizations(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.profile(root)
            older=ROOT/'tests/fixtures/v56_aikya_requirements.py'
            target=root/'aikya/scripts/harness/aikya_requirements.py'
            target.parent.mkdir(parents=True)
            target.write_bytes(older.read_bytes())
            install.install(root,p,{'modules':[],'findings':[]})
            self.assertEqual(runtime_support.generated_bytes('aikya_requirements.py'),target.read_bytes())
            self.assertEqual(older.read_bytes(),(root/'.harness/backup-v56/aikya_requirements.py').read_bytes())
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.profile(root)
            target=root/'aikya/scripts/harness/aikya_requirements.py'
            target.parent.mkdir(parents=True)
            target.write_text('# CUSTOMIZED DETECTOR\n')
            install.install(root,p,{'modules':[],'findings':[]})
            self.assertEqual('# CUSTOMIZED DETECTOR\n',target.read_text())

    def test_deployed_infra_script_is_cli_readable(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.profile(root,infrastructure=self.selection())
            install.install(root,p,{'modules':[],'findings':[]})
            result=subprocess.run([sys.executable,str(root/'aikya/scripts/harness/infrastructure.py'),'plan','--target',str(root)],
                                  cwd=root,capture_output=True,text=True,timeout=10)
            self.assertEqual(0,result.returncode,result.stderr)
            self.assertIn('infra/terraform/versions.tf',result.stdout)

if __name__=='__main__':
    unittest.main()
