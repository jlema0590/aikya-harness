#!/usr/bin/env python3
"""Documentación por petición: snapshots locales, verificación de cobertura y CI.

Solo stdlib. No lee contenido de prompts ni secretos; almacena hash, categoría y rutas.
Nota: un guardrail verifica modificaciones/estructura, NO exactitud semántica.
"""
from __future__ import annotations
from aikya.resource_paths import project_root
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone
from uuid import uuid4

ROOT = project_root()
STATE = ROOT / '.harness' / 'state'
IGNORED = {'.git', '.harness', 'node_modules', '.next', '.nuxt', '.venv',
           'venv', 'dist', 'build', 'target', 'obj', 'bin', 'coverage',
           '.gradle', '.idea', '.dart_tool', 'Pods', '.terraform', '__pycache__'}
CONFIG_FILES = {'pom.xml','build.gradle','build.gradle.kts','package.json',
                'tsconfig.json','Dockerfile','docker-compose.yml','compose.yaml',
                'settings.gradle','settings.gradle.kts', 'pubspec.yaml',
                'global.json', 'gradle.properties'}
DOCS_REQUIRED = ('aikya/docs/overview.md','aikya/docs/indice.md',
                 'aikya/docs/architecture/architecture-overview.md','aikya/docs/tools/token-policy.md')


def normalized_session(session: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]', '_', session or 'default')[:80] or 'default'


def file_map() -> dict[str,str]:
    """Incremental local snapshot; rehash only files with changed stat metadata."""
    index_file = STATE / 'hash-index.json'
    try:
        index = json.loads(index_file.read_text(encoding='utf8'))
        if not isinstance(index, dict):
            index = {}
    except (OSError, UnicodeError, ValueError):
        index = {}
    mapping: dict[str,str] = {}
    new_index: dict[str,dict] = {}
    seen = 0
    for base, dirs, names in os.walk(ROOT, followlinks=False):
        dirs[:] = [d for d in dirs if d not in IGNORED and not d.startswith('.git')
                   and not (Path(base)==ROOT/'.aikya' and d=='runtime')]
        for name in names:
            path = Path(base) / name
            rel = path.relative_to(ROOT).as_posix()
            if name.startswith('.env') or path.is_symlink() or not path.is_file():
                continue
            if not (path.suffix.lower()=='.md' or is_source(rel)):
                continue
            try:
                st = path.stat()
                signature = [st.st_size, st.st_mtime_ns, st.st_ctime_ns]
                old = index.get(rel)
                if isinstance(old, dict) and old.get('stat') == signature and isinstance(old.get('hash'), str):
                    digest = old['hash']
                elif st.st_size > 3_000_000:
                    digest = f'large:{st.st_size}:{st.st_mtime_ns}:{st.st_ctime_ns}'
                else:
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                mapping[rel] = digest
                new_index[rel] = {'stat': signature, 'hash': digest}
            except OSError:
                continue
            seen += 1
            if seen >= 12000:
                mapping['__TRUNCATED__'] = 'true'
                break
        if seen >= 12000:
            break
    # Cache is an optimization: failure to write must not affect correctness.
    try:
        STATE.mkdir(parents=True, exist_ok=True)
        tmp = index_file.with_name('hash-index-' + uuid4().hex + '.json')
        tmp.write_text(json.dumps(new_index, separators=(',', ':')), encoding='utf8')
        tmp.replace(index_file)
    except OSError:
        pass
    return mapping


def is_source(path: str) -> bool:
    name = path.rsplit('/',1)[-1]
    if path.startswith('.claude/skills/') and name == 'SKILL.md':
        return True
    if name in CONFIG_FILES or name.endswith(('.csproj','.sln','.xcodeproj','.xcworkspace')):
        return True
    return (path.startswith(('apps/','api/','backend/','server/','src/','web/',
                             'client/','frontend/','mobile/','android/','ios/',
                             'packages/','tests/','test/','infra/','.github/',
                             '.gitlab/')) or
            path.endswith(('.java','.kt','.kts','.swift','.cs','.tsx','.ts',
                           '.jsx','.js','.vue','.dart','.go','.py','.tf')))


def kind_from_prompt(prompt: str) -> str:
    """Word-boundary classification; suggestions only, never sole proof of changed files."""
    p = prompt.lower()
    # Read-only questions should not trigger an action category merely because
    # they mention bugs, Docker or architecture.
    interrogative = re.search(r'^\s*¿?\s*(qué|que|cuál|cual|cómo|como|por qué|why|what|how|explain)\b', p)
    action = re.search(r'\b(corrige|corrigir|corregir|fix|implementa|añade|agrega|crea|despliega|refactoriza)\b', p)
    if interrogative and not action:
        return 'general'
    keywords = {
        'security': ('seguridad', 'vulnerabilidad', 'autenticación', 'autorización',
                     'security', 'cve', 'secrets'),
        'bug': ('bug', 'error', 'fix', 'corrige', 'corregir', 'fallo',
                'regresión', 'defecto'),
        'architecture': ('arquitectura', 'refactor', 'migración',
                         'architecture', 'refactoring'),
        'operations': ('devops', 'deploy', 'pipeline', 'docker',
                       'kubernetes', 'terraform', 'ci/cd'),
        'feature': ('feature', 'funcionalidad', 'implementa', 'crear',
                    'añade', 'agrega', 'endpoint', 'pantalla'),
    }
    matches = [kind for kind, terms in keywords.items()
               if any(re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', p)
                      for term in terms)]
    return '+'.join(matches) if matches else 'general'


def start_request(session: str, prompt: str) -> dict:
    STATE.mkdir(parents=True,exist_ok=True)
    request_id = 'REQ-'+datetime.now(timezone.utc).strftime('%Y%m%d')+'-'+uuid4().hex[:8]
    state = {'request_id':request_id, 'session_id':normalized_session(session),
             'kind':kind_from_prompt(prompt),
             'prompt_sha256':hashlib.sha256(prompt.encode('utf8')).hexdigest(),
             'started_utc':datetime.now(timezone.utc).isoformat(),
             'baseline':file_map()}
    # Sólo escribe estado local; nunca persiste el texto completo del prompt.
    path = STATE / (normalized_session(session)+'.json')
    path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return state


def load_state(session: str) -> dict | None:
    path = STATE/(normalized_session(session)+'.json')
    try:
        data = json.loads(path.read_text(encoding='utf8'))
        return data if isinstance(data,dict) and 'baseline' in data else None
    except (OSError,ValueError):
        return None


def changes(baseline: dict[str,str], current: dict[str,str]) -> tuple[list[str],list[str]]:
    code = sorted(p for p in baseline.keys() | current.keys()
                  if p != '__TRUNCATED__' and is_source(p) and not p.startswith('aikya/docs/')
                  and baseline.get(p) != current.get(p))
    docs = sorted(p for p in baseline.keys() | current.keys()
                  if p.startswith('aikya/docs/') and baseline.get(p) != current.get(p))
    return code,docs


def affected_docs(kind: str, paths: list[str]) -> list[str]:
    required: set[str] = set()
    kinds=set(kind.split('+'))
    if 'feature' in kinds:
        required.update(('aikya/docs/features/index.md','aikya/docs/plan/roadmap.md'))
    if 'bug' in kinds:
        required.add('aikya/docs/bugs/bugs.md')
    if 'security' in kinds:
        required.add('aikya/docs/security/security.md')
    if 'architecture' in kinds:
        required.add('aikya/docs/architecture/architecture-overview.md')
    if 'operations' in kinds:
        required.add('aikya/docs/operations/deployment.md')
    for path in paths:
        if path.startswith('.claude/skills/'):
            required.add('aikya/docs/skills.md')
        p = path.lower()
        # El sistema de diseño sólo se exige si existe una interfaz y se toca una pantalla/componente.
        if (p.endswith(('.tsx','.jsx','.vue','.css','.scss','.svelte')) or
            any(part in p for part in ('/screens/','/components/','/pages/','/views/','/ui/'))) and (
            p.startswith(('apps/web/','apps/frontend/','frontend/','web/','client/','src/','apps/mobile/','apps/android/','apps/ios/','mobile/'))):
            required.add('aikya/docs/design/design-system.md')
        if p.startswith(('tests/','test/','aikya/test/')) or '/test/' in p or '/tests/' in p or p.endswith(('.test.ts','.spec.ts')):
            required.add('aikya/docs/plan/testing.md')
        if p.startswith(('infra/','.github/','.gitlab/')) or any(w in p for w in ('docker','terraform','k8s','helm')):
            required.add('aikya/docs/operations/deployment.md')
        if any(w in p for w in ('security','auth','permission','credential')):
            required.add('aikya/docs/security/security.md')
        if any(w in p for w in ('telemetry','observab','tracing','metrics')):
            required.add('aikya/docs/operations/observability.md')
        if any(w in p for w in ('architecture','module','schema','migration')):
            required.add('aikya/docs/architecture/architecture-overview.md')
    if not required:
        required.add('aikya/docs/overview.md')
    return sorted(required)


def nonplaceholder(path: Path) -> bool:
    try:
        s = path.read_text(encoding='utf8')
    except (OSError,UnicodeError):
        return False
    return len(s.strip()) >= 80 and 'TODO: completar' not in s and 'PENDIENTE_DE_COMPLETAR' not in s and 'TODO: complete' not in s and 'PENDING_COMPLETION' not in s


def validate_request(state: dict, now: dict|None=None) -> tuple[bool,list[str]]:
    now = now if now is not None else file_map()
    from aikya.documentation.layout import validate_generated_document_paths
    candidates=[p for p in now if state['baseline'].get(p)!=now[p]]
    path_errors=validate_generated_document_paths(ROOT,candidates)
    if path_errors:return False,path_errors
    changed, updated = changes(state['baseline'],now)
    if not changed:
        return True,['Sin cambios en código/infraestructura durante esta petición: no se requieren modificaciones documentales.']
    req = state['request_id']
    change_path = 'aikya/docs/changes/'+req+'.md'
    required = affected_docs(state['kind'],changed)
    # A concrete feature contract can cover a request without an empty catalog/roadmap update.
    if 'feature' in state['kind'].split('+'):
        feature_specs=sorted(p for p in updated
                             if re.fullmatch(r'aikya/docs/features/[a-z0-9]+(?:-[a-z0-9]+)*/spec\.md',p)
                             and nonplaceholder(ROOT/p))
        if feature_specs:
            required=[p for p in required if p not in ('aikya/docs/features/index.md','aikya/docs/plan/roadmap.md')]+feature_specs
    errors: list[str] = []
    if '__TRUNCATED__' in state['baseline'] or '__TRUNCATED__' in now:
        errors.append('Inventario de archivos truncado; revisa manualmente los cambios.')
    if change_path not in updated or not nonplaceholder(ROOT/change_path):
        errors.append(f'Falta bitácora sustantiva de la petición: {change_path}.')
    else:
        content = (ROOT/change_path).read_text(encoding='utf8')
        # Accept a complete ES or EN heading set. Historical Spanish logs remain valid.
        expected_sets = (('## Changes', '## Evidence', '## Updated documents'),
                         ('## Cambios', '## Evidencias', '## Documentos actualizados'))
        if not any(all(heading in content for heading in headings)
                   for headings in expected_sets):
            errors.append('Change logs require a complete, consistent EN or ES heading set.')
        if not any(p in content for p in changed):
            errors.append('La bitácora no referencia ninguno de los archivos de código modificados.')
        if not any(doc in content for doc in required):
            errors.append('La bitácora no referencia los documentos obligatorios.')
    for doc in required:
        if doc not in updated or not nonplaceholder(ROOT/doc):
            errors.append(f'Falta actualizar documento afectado: {doc}')
    return not errors, ([f'Cambios en código: {", ".join(changed[:12])}',
                         f'Documentos requeridos: {", ".join(required)}'] + errors)


def validate_base() -> list[str]:
    errors=[f'No existe o está vacío: {p}' for p in DOCS_REQUIRED
            if not (ROOT/p).is_file() or not (ROOT/p).read_text(encoding='utf8').strip()]
    from aikya.documentation.layout import validate_layout
    return errors+validate_layout(ROOT)


def git_changed(base: str) -> list[str]:
    # Evita shell=True; sólo nombres, no se leen secretos ni contenido de archivos.
    command = ['git','diff','--name-only','--diff-filter=ACDMRT',f'{base}...HEAD']
    res = subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=15)
    if res.returncode:
        res = subprocess.run(['git','diff','--name-only','--diff-filter=ACDMRT',base,'HEAD'],
                             cwd=ROOT,capture_output=True,text=True,timeout=15)
    if res.returncode:
        raise ValueError('No se pudo resolver base Git: '+res.stderr.strip())
    return sorted({x.strip() for x in res.stdout.splitlines() if x.strip()})


def validate_ci(paths: list[str]) -> tuple[bool,list[str]]:
    from aikya.documentation.layout import validate_generated_document_paths
    path_errors=validate_generated_document_paths(ROOT,paths)
    if path_errors:return False,path_errors
    changed = [p for p in paths if is_source(p) and not p.startswith('aikya/docs/')]
    if not changed:
        return True,['Sin código modificado en el diff: documentación sin cambios permitida.']
    docs = {p for p in paths if p.startswith('aikya/docs/')}
    # El tipo exacto de la petición no se infiere en CI; se valida categoría por rutas +
    # al menos un doc funcional, con revisión humana para semántica.
    required = [p for p in affected_docs('general',changed) if p != 'aikya/docs/overview.md']
    if not any(x.startswith(('aikya/docs/features/','aikya/docs/bugs/','aikya/docs/architecture/','aikya/docs/operations/','aikya/docs/security/','aikya/docs/plan/','aikya/docs/design/')) or x=='aikya/docs/overview.md' for x in docs):
        required.append('una página temática de aikya/docs/ (además de la bitácora)')
    errors = [f'Falta documento afectado en diff: {p}' for p in required if p not in docs and not p.startswith('una página')]
    if 'una página temática de aikya/docs/ (además de la bitácora)' in required:
        errors.append('Falta actualizar al menos un documento temático de aikya/docs/.')
    logs = [p for p in docs if re.fullmatch(r'aikya/docs/changes/REQ-\d{8}-[a-f0-9]{8}\.md',p)]
    if not logs:
        errors.append('Falta al menos un aikya/docs/changes/REQ-*.md en el diff.')
    return not errors,errors or ['Validación estructural de documentación del diff: OK.']


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description='Validar cobertura documental por petición/CI')
    parser.add_argument('mode',choices=['base','status','ci'])
    parser.add_argument('--session',default='',help='ID de sesión (vacío: auto si sólo hay un estado local)')
    parser.add_argument('--base')
    args=parser.parse_args(argv)
    base_errors=validate_base()
    if base_errors:
        print('\n'.join(base_errors),file=sys.stderr)
        return 1
    if args.mode=='base':
        print('Estructura documental: OK')
        return 0
    if args.mode=='ci':
        if not args.base:
            print('--base requerido para CI; no se omite validación.',file=sys.stderr)
            return 2
        try:
            ok,messages=validate_ci(git_changed(args.base))
        except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
            print(str(exc),file=sys.stderr)
            return 2
    else:
        session=args.session
        if not session:
            candidates=list(STATE.glob('*.json')) if STATE.exists() else []
            if len(candidates)==1:
                session=candidates[0].stem
            else:
                print(f'Se encontraron {len(candidates)} sesiones: indica --session <id>.',file=sys.stderr)
                return 2
        state=load_state(session)
        if state is None:
            print('No se encontró la petición activa. Ejecuta /documentation-sync.',file=sys.stderr)
            return 2
        ok,messages=validate_request(state)
    print('\n'.join(messages))
    return 0 if ok else 1

if __name__=='__main__':
    sys.exit(main())
