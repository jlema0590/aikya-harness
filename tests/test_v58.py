"""Acceptance v5.8: autonomous Development, Infrastructure and DevOps modes."""
import runtime_support
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aikya.installation import facade as install
from aikya.discovery import infrastructure as infrastructure_profile
from aikya.catalogs import engineering as engineering_catalog
from aikya.installation import requirements as aikya_requirements
from aikya.documentation import bootstrap as doc_bootstrap

def module(path,name):
    spec=runtime_support.module_spec(name,path)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj);obj=getattr(obj,'_module',obj)
    return getattr(obj, '_module', obj)

GEN=module(ROOT/'src/aikya/resources/project_template/scripts/harness/infrastructure.py','infrastructure_v58')
SCAFFOLD=module(ROOT/'src/aikya/resources/project_template/scripts/harness/scaffold.py','scaffold_v58')

class AutonomousModeTests(unittest.TestCase):
    def infra(self,**kw):
        base={'provider':'aws','iac':'terraform','configuration_management':'none',
              'containers':{'enabled':False,'compose':False},'orchestration':'none',
              'deployment_method':'none','environments':['dev','prod'],
              'image_repository':'','container_port':None}
        return {**base,**kw}

    def profile(self,target,kind='infrastructure',**kw):
        base={'project_type':kind,'mode':'new','repository_layout':'singlerepo',
              'name':'platform','backend':'none','frontend':'none','mobile':'none',
              'backend_framework':'none','mobile_framework':'none','package_manager':'none',
              'deployment':'none','infrastructure':self.infra()}
        return install.validated({**base,**kw},target)

    def test_legacy_profile_defaults_to_development(self):
        with tempfile.TemporaryDirectory() as d:
            raw=json.loads((ROOT/'examples/next-react/answers.json').read_text())
            p=install.validated(raw,Path(d))
            self.assertEqual('development',p['project_type'])
            self.assertEqual('next',p['backend'])

    def test_terraform_only_no_application_validation(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.profile(Path(d))
            self.assertEqual('infrastructure',p['project_type'])
            self.assertEqual('none',p['backend'])
            self.assertEqual('terraform',p['infrastructure']['iac'])

    def test_ansible_only_valid(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.profile(Path(d),infrastructure=self.infra(iac='none',configuration_management='ansible'))
            self.assertEqual('ansible',p['infrastructure']['configuration_management'])

    def test_empty_infrastructure_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'Infrastructure requiere'):
                self.profile(Path(d),infrastructure=self.infra(iac='none'))

    def test_no_application_stack_permitted_in_specialized_mode(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, 'cannot include an application stack'):
                self.profile(Path(d),backend='java',backend_framework='spring-boot')

    def test_devops_kubernetes_from_existing_image_without_docker_local(self):
        with tempfile.TemporaryDirectory() as d:
            info=self.infra(iac='none',provider='none',
                 containers={'enabled':False,'compose':False},
                 orchestration='kubernetes',deployment_method='helm',
                 image_repository='ghcr.io/example/service:1.2.0',container_port=8080,
                 source_kind='image')
            p=self.profile(Path(d),'devops',infrastructure=info)
            tools=aikya_requirements.required_tools(p)
            self.assertIn('helm',tools)
            self.assertNotIn('docker',tools)
            self.assertNotIn('node',tools)

    def test_devops_docker_compose_existing_image_no_source_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            info=self.infra(iac='none',provider='none',
                 containers={'enabled':True,'compose':True},source_kind='image',
                 image_repository='ghcr.io/example/api:1.0.0',container_port=3000)
            p=self.profile(root,'devops',infrastructure=info)
            artifacts,pending=GEN.specs(root,p)
            self.assertNotIn('Dockerfile',artifacts)
            self.assertIn('compose.apps.yaml',artifacts)
            self.assertIn('ghcr.io/example/api:1.0.0',artifacts['compose.apps.yaml'])

    def test_devops_only_no_app_directories_on_install(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            p=self.profile(root,'devops',infrastructure=self.infra(iac='none',
                containers={'enabled':True,'compose':True},source_kind='image',
                image_repository='ghcr.io/example/api:1.0.0',container_port=8080))
            install.install(root,p,{'modules':[],'findings':[]})
            for forbidden in ('apps','packages','contracts','package.json','pnpm-workspace.yaml',
                              'infra/docker/compose.example.yaml'):
                self.assertFalse((root/forbidden).exists(),forbidden)
            for expected in ('aikya/docs/README.md','aikya/docs/infrastructure/plan.md',
                             'aikya/scripts/harness/infrastructure.py','aikya/test/test_harness.py'):
                self.assertTrue((root/expected).exists(),expected)
            obj=json.loads((root/'harness.json').read_text())
            self.assertFalse(any(x['name'].startswith(('backend:','frontend:','mobile:','project:test')) for x in obj['checks']))
            self.assertIn('infra:static',[x['name'] for x in obj['checks']])
            self.assertNotIn('apps/',(root/'aikya/docs/overview.md').read_text())

    def test_terraform_only_install_generates_no_devops_or_app_scaffold(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.profile(root)
            install.install(root,p,{'modules':[],'findings':[]})
            self.assertFalse((root/'apps').exists())
            self.assertFalse((root/'infra/docker').exists())
            self.assertTrue((root/'aikya/docs/infrastructure/plan.md').is_file())
            files,pending=GEN.specs(root,p)
            self.assertIn('infra/terraform/versions.tf',files)
            self.assertFalse(any(x.startswith('Dockerfile') for x in files))
            self.assertFalse(any('/helm/' in x for x in files))

    def test_terraform_requirements_select_only_terraform(self):
        with tempfile.TemporaryDirectory() as d:
            tools=aikya_requirements.required_tools(self.profile(Path(d)))
            self.assertIn('terraform',tools)
            for forbidden in ('node','java','docker','ansible','kubectl','helm'):
                self.assertNotIn(forbidden,tools)

    def test_specialized_agent_selection_does_not_activate_developers(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.profile(Path(d))
            selected=engineering_catalog.discover(Path(d),p,[{'role':'backend','technology':'java','path':'src'}])
            self.assertIn('terraform-engineer',selected['agents'])
            self.assertNotIn('java-developer',selected['agents'])
            self.assertNotIn('node-backend-developer',selected['agents'])
            self.assertNotIn('microservices-architect',selected['agents'])

    def test_helm_existing_chart_is_read_only_and_validatable(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            chart=root/'charts/company'
            chart.mkdir(parents=True)
            (chart/'Chart.yaml').write_text('apiVersion: v2\nname: company\nversion: 0.1.0\n')
            info=self.infra(iac='none',provider='none',orchestration='kubernetes',
                 deployment_method='helm',source_kind='chart',
                 helm_chart_mode='existing',helm_chart_path='charts/company')
            p=self.profile(root,'devops',infrastructure=info)
            artifacts,_=GEN.specs(root,p)
            self.assertFalse(any('/templates/' in x or x.endswith('Chart.yaml') for x in artifacts))
            calls=[]
            def runner(command,**kwargs):
                calls.append(command)
                return SimpleNamespace(returncode=0,stdout='',stderr='')
            with patch.object(GEN.shutil,'which',return_value='/fake/helm'):
                status,rows=GEN.validate(root,p,executor=runner)
            self.assertEqual(0,status)
            self.assertEqual(2,len(calls))
            self.assertEqual('helm',calls[0][0])
            self.assertEqual((chart/'Chart.yaml').read_text(),'apiVersion: v2\nname: company\nversion: 0.1.0\n')

    def test_helm_charts_validate_when_root_is_a_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            real=Path(d)/'real'
            (real/'charts/company').mkdir(parents=True)
            (real/'charts/company/Chart.yaml').write_text('apiVersion: v2\nname: company\nversion: 0.1.0\n')
            (real/'infra/helm/charts/web').mkdir(parents=True)
            (real/'infra/helm/charts/web/Chart.yaml').write_text('apiVersion: v2\nname: web\nversion: 0.1.0\n')
            root=Path(d)/'link'
            root.symlink_to(real,target_is_directory=True)
            for mode,expected in (('existing','charts/company'),('create','infra/helm/charts/web')):
                with self.subTest(mode=mode):
                    info=self.infra(iac='none',provider='none',orchestration='kubernetes',
                         deployment_method='helm',source_kind='chart',
                         helm_chart_mode=mode,helm_chart_path='charts/company' if mode=='existing' else '')
                    calls=[]
                    def runner(command,**kwargs):
                        calls.append(command)
                        return SimpleNamespace(returncode=0,stdout='',stderr='')
                    with patch.object(GEN.shutil,'which',return_value='/fake/helm'):
                        status,_=GEN.validate(root,self.profile(root,'devops',infrastructure=info),executor=runner)
                    self.assertEqual(0,status)
                    self.assertEqual([expected,expected],[c[-1] for c in calls])

    def test_generated_chart_symlinked_outside_project_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            outside=Path(d)/'outside'
            outside.mkdir()
            (outside/'Chart.yaml').write_text('apiVersion: v2\nname: evil\nversion: 0.1.0\n')
            root=Path(d)/'project'
            (root/'infra/helm/charts').mkdir(parents=True)
            (root/'infra/helm/charts/evil').symlink_to(outside,target_is_directory=True)
            info=self.infra(iac='none',provider='none',orchestration='kubernetes',
                 deployment_method='helm',source_kind='chart',helm_chart_mode='create')
            calls=[]
            with patch.object(GEN.shutil,'which',return_value='/fake/helm'):
                status,rows=GEN.validate(root,self.profile(root,'devops',infrastructure=info),
                                         executor=lambda c,**k: calls.append(c))
            self.assertEqual(2,status)
            self.assertIn('fuera del proyecto',rows[0])
            self.assertEqual([],calls)

    def test_existing_helm_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            info=self.infra(iac='none',provider='none',orchestration='kubernetes',
                 deployment_method='helm',source_kind='chart',
                 helm_chart_mode='existing',helm_chart_path='../outside')
            with self.assertRaisesRegex(ValueError,'relativa'):
                self.profile(Path(d),'devops',infrastructure=info)

    def test_helm_existing_missing_chart_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            p=self.profile(root,'devops',infrastructure=self.infra(
                 iac='none',provider='none',orchestration='kubernetes',
                 deployment_method='helm',helm_chart_mode='existing',
                 helm_chart_path='charts/missing'))
            code,lines=GEN.validate(root,p)
            self.assertEqual(2,code)
            self.assertTrue(any('NOT_CONFIGURED' in x for x in lines))

    def test_deployment_variants_are_mutually_exclusive(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for method in ('yaml','kustomize','helm'):
                p=self.profile(root,'devops',infrastructure=self.infra(
                    iac='none',provider='none',orchestration='kubernetes',
                    deployment_method=method,source_kind='image',
                    image_repository='ghcr.io/example/app:1.0.0',container_port=8080))
                files,_=GEN.specs(root,p)
                self.assertEqual(method=='helm',any(x.endswith('/Chart.yaml') for x in files))
                self.assertEqual(method=='kustomize',any(x.endswith('kustomization.yaml') for x in files))
                self.assertEqual(method in ('yaml','kustomize'),'infra/kubernetes/base/deployment.yaml' in files)

    def test_app_scaffold_rejected_in_autonomous_modes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.profile(root)
            commands,notes=SCAFFOLD.command_plans(p)
            self.assertEqual([],commands)
            self.assertEqual(2,SCAFFOLD.apply(p,root,True))

    def test_does_not_overwrite_preexisting_infra(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.profile(root)
            path=root/'infra/terraform/versions.tf'
            path.parent.mkdir(parents=True)
            path.write_text('USER CONTENT\n')
            code,log=GEN.generate(root,p,approved=True)
            self.assertEqual(0,code)
            self.assertEqual('USER CONTENT\n',path.read_text())
            self.assertIn('CONSERVADO infra/terraform/versions.tf',log)

    def test_example_profiles_are_valid(self):
        for file in sorted((ROOT/'examples').glob('*/answers.json')):
            with tempfile.TemporaryDirectory() as d, self.subTest(name=file.parent.name):
                p=install.validated(json.loads(file.read_text()),Path(d))
                self.assertIn(p['project_type'],('development','infrastructure','devops'))

if __name__=='__main__':
    unittest.main()
