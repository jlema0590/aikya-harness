import runtime_support
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aikya.installation import facade as install
from aikya.documentation.bootstrap import pages,infra_files


def import_from(path,name):
    spec=runtime_support.module_spec(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod);mod=getattr(mod,'_module',mod)
    return getattr(mod, '_module', mod)

GUARD=import_from(ROOT/'src/aikya/resources/project_template/scripts/harness/docs_guard.py','docs_guard_v3')
SCAFFOLD=import_from(ROOT/'src/aikya/resources/project_template/scripts/harness/scaffold.py','scaffold_v3')


def profile(mode='new',**changes):
    p={'mode':mode,'name':'Prueba','backend':'dotnet','backend_framework':'aspnet-core',
       'frontend':'react','mobile':'none','mobile_framework':'none','android_language':'none',
       'ios_ui':'none','architecture':'modular-monolith','database':'postgresql',
       'ci':'github-actions','deployment':'docker','package_manager':'npm',
       'api_style':'rest','auth':'oidc-oauth2','observability':'opentelemetry',
       'quality':'unit+integration','frontend_rendering':'spa','runtime_versions':'','notes':''}
    p.update(changes)
    return p


class V3Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'repo'
        self.original_root=GUARD.ROOT
        self.original_state=GUARD.STATE
        GUARD.ROOT=self.root
        GUARD.STATE=self.root/'.harness/state'
        self.addCleanup(setattr,GUARD,'ROOT',self.original_root)
        self.addCleanup(setattr,GUARD,'STATE',self.original_state)
        self.root.mkdir()

    def install(self,p=None):
        install.install(self.root,p or profile(),{'modules':[],'findings':[]})

    def test_install_creates_living_docs_ci_infra_and_hooks(self):
        self.install()
        self.assertEqual([],GUARD.validate_base())
        self.assertTrue((self.root/'aikya/docs/security/security.md').is_file())
        self.assertTrue((self.root/'aikya/docs/plan/roadmap.md').is_file())
        self.assertTrue((self.root/'aikya/docs/decisions/0001-entrevista-stack.md').is_file())
        self.assertTrue((self.root/'compose.yaml').is_file())
        self.assertTrue((self.root/'.github/workflows/harness.yml').is_file())
        settings=json.loads((self.root/'.claude/settings.json').read_text())
        self.assertIn('Stop',settings['hooks'])
        self.assertIn('UserPromptSubmit',settings['hooks'])
        self.assertFalse((self.root/'apps/api').exists())  # sin generadores ni red
        self.assertIn('docs:structure', [c['name'] for c in json.loads((self.root/'harness.json').read_text())['checks']])

    def test_no_code_changed_needs_no_log(self):
        self.install()
        state=GUARD.start_request('session-1','¿Qué representa esta arquitectura?')
        ok,notes=GUARD.validate_request(state)
        self.assertTrue(ok,notes)
        self.assertFalse((self.root/'aikya/docs/changes'/f'{state["request_id"]}.md').exists())
        self.assertNotIn('¿Qué representa',str(state))

    def test_feature_requires_docs_and_per_request_changelog(self):
        self.install()
        state=GUARD.start_request('session-1','Implementa endpoint para catálogo de productos')
        (self.root/'apps/api').mkdir(parents=True)
        (self.root/'apps/api/server.ts').write_text('export const route="/catalog";\n')
        ok,errors=GUARD.validate_request(state)
        self.assertFalse(ok)
        self.assertTrue(any('aikya/docs/features/index.md' in m for m in errors))
        self.assertTrue(any('aikya/docs/plan/roadmap.md' in m for m in errors))
        self.assertTrue(any('REQ-' in m for m in errors))
        for doc in ('aikya/docs/features/index.md','aikya/docs/plan/roadmap.md'):
            (self.root/doc).parent.mkdir(parents=True,exist_ok=True)
            with (self.root/doc).open('a') as f:
                f.write('\nSe añade endpoint catálogo con criterios de aceptación y regresión; el alcance confirmado incluye la ruta y los resultados de pruebas.\n')
        req=self.root/'aikya/docs/changes'/f'{state["request_id"]}.md'
        req.write_text(f'''# {state["request_id"]} — catálogo\n\n## Cambios\n- `apps/api/server.ts`: se implementa endpoint catálogo.\n\n## Evidencias\n- No ejecutado: falta SDK de la aplicación, pendiente de configurar.\n\n## Documentos actualizados\n- `aikya/docs/features/index.md`: nueva ruta.\n- `aikya/docs/plan/roadmap.md`: nueva tarea.\n''')
        ok,messages=GUARD.validate_request(state)
        self.assertTrue(ok,messages)

    def test_bug_requires_bug_docs(self):
        self.install()
        state=GUARD.start_request('a','Corrige un bug en el login')
        (self.root/'apps/api').mkdir(parents=True)
        (self.root/'apps/api/index.ts').write_text('export const login = ()=> true;')
        ok,msgs=GUARD.validate_request(state)
        self.assertFalse(ok)
        self.assertTrue(any('aikya/docs/bugs/bugs.md' in m for m in msgs))

    def test_security_path_requires_security_page(self):
        self.install()
        state=GUARD.start_request('sec','Actualiza el módulo de autenticación')
        (self.root/'apps/api').mkdir(parents=True)
        (self.root/'apps/api/auth.ts').write_text('export const auth=true;')
        _,msgs=GUARD.validate_request(state)
        self.assertTrue(any('aikya/docs/security/security.md' in m for m in msgs))

    def test_docs_preserved_if_existing(self):
        page=self.root/'aikya/docs/overview.md'
        page.parent.mkdir(parents=True,exist_ok=True)
        page.write_text('# Documento propio\nRequisitos específicos.\n')
        (self.root/'CLAUDE.md').write_text('# Instrucciones propias\n')
        self.install(profile('existing'))
        self.assertEqual('# Documento propio\nRequisitos específicos.\n',page.read_text())
        self.assertEqual('# Instrucciones propias\n',(self.root/'CLAUDE.md').read_text())
        self.assertTrue((self.root/'.claude/rules/01-documentation-policy.md').exists())

    def test_scaffold_plan_covers_native_and_frameworks(self):
        p=profile(backend='java',backend_framework='spring-boot',frontend='vue',
                  mobile='both',mobile_framework='native',android_language='kotlin',ios_ui='swiftui')
        commands,manual=SCAFFOLD.command_plans(p)
        self.assertEqual(['apps/web'],[x['creates'] for x in commands])
        self.assertTrue(any('Android Studio' in x for x in manual))
        self.assertTrue(any('Xcode' in x for x in manual))
        self.assertTrue(any('Spring Initializr' in x for x in manual))

    def test_scaffold_apply_prevents_overwrite(self):
        p=profile()
        (self.root/'apps/api').mkdir(parents=True)
        with patch.object(SCAFFOLD.shutil,'which',return_value='/usr/bin/mock'):
            self.assertEqual(2,SCAFFOLD.apply(p,self.root,True,runner=lambda *a,**k: self.fail('must not run')))

    def test_ci_enforces_security_docs_and_changelog(self):
        paths=['apps/api/auth.ts','aikya/docs/changes/REQ-20261018-abcdef12.md','aikya/docs/security/security.md']
        ok,msgs=GUARD.validate_ci(paths)
        self.assertTrue(ok,msgs)
        ok,msgs=GUARD.validate_ci(['apps/api/auth.ts','aikya/docs/features/index.md'])
        self.assertFalse(ok)

    def test_end_to_end_hook_stop_blocks_until_documented(self):
        self.install()
        env={**os.environ,'CLAUDE_PROJECT_DIR':str(self.root)}
        submit=subprocess.run([sys.executable,str(self.root/'.claude/hooks/request_docs.py')],
                              input=json.dumps({'session_id':'abc','prompt':'Implementa una feature'}),
                              text=True,capture_output=True,env=env)
        self.assertEqual(0,submit.returncode,submit.stderr)
        request_id=GUARD.load_state('abc')['request_id']
        (self.root/'apps/api').mkdir(parents=True)
        (self.root/'apps/api/app.ts').write_text('export default 2;')
        stop=subprocess.run([sys.executable,str(self.root/'.claude/hooks/stop_docs.py')],
                            input=json.dumps({'session_id':'abc','stop_hook_active':False}),
                            text=True,capture_output=True,env=env)
        self.assertEqual(0,stop.returncode,stop.stderr)
        self.assertEqual('block',json.loads(stop.stdout)['decision'])
        self.assertIn(request_id,stop.stdout)


if __name__=='__main__':
    unittest.main()
