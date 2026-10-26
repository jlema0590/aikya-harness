#!/usr/bin/env python3
"""Scaffolding opt-in con generadores oficiales. Python 3.9+ stdlib.

plan nunca ejecuta ni escribe. apply solicita confirmación, no ejecuta shell
ni sobrescribe módulos ya existentes. Para stacks sin CLI fiable hay guía manual.
"""
from __future__ import annotations
from aikya.resource_paths import project_root
import argparse
import json
import tempfile
import re
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = project_root()


def load_profile(root: Path=ROOT) -> dict:
    path=root/'.harness/project-profile.json'
    profile=json.loads(path.read_text(encoding='utf8'))
    if not isinstance(profile,dict) or not isinstance(profile.get('decisions'),dict):
        raise ValueError('Perfil inválido: instala el harness antes de hacer scaffolding')
    return profile['decisions']


def command_plans(p:dict) -> tuple[list[dict],list[str]]:
    if p.get('project_type','development')!='development':
        return [], ['Modo Infrastructure/DevOps: usa /aikya-infra plan/generate/validate.']
    commands=[]
    manual=[]
    pm=p.get('package_manager')
    if pm not in ('npm','pnpm','yarn','bun'):
        pm='npm'
    def add(label,cmd,relative_path,dependency=None):
        commands.append({'label':label,'command':cmd,'creates':relative_path,
                         'requires':dependency or cmd[0]})
    layout=p.get('repository_layout','monorepo')
    if layout not in ('monorepo','singlerepo'):
        raise ValueError('repository_layout no válido')
    if layout == 'singlerepo':
        count=int(p.get('backend','none')!='none')
        count+=int(p.get('frontend','none')!='none' and not (p.get('backend')=='next' and p.get('frontend')=='react'))
        count+=2 if p.get('mobile')=='both' and p.get('mobile_framework')=='native' else int(p.get('mobile') not in (None,'none'))
        if count != 1 and p.get('mode')=='new':
            raise ValueError('singlerepo necesita una sola aplicación. Selecciona monorepo.')
    def destination(default):
        return default if layout=='monorepo' else '.'
    backend=p.get('backend')
    frontend=p.get('frontend')
    mobile=p.get('mobile')
    if backend=='dotnet':
        template='web' if p.get('backend_framework')=='minimal-api' else 'webapi'
        add('Backend ASP.NET Core',['dotnet','new',template,'-o',destination('apps/api')],destination('apps/api'))
    elif backend=='next':
        add('Aplicación Next.js + React',
            ['npx','create-next-app@latest',destination('apps/web'),'--typescript','--eslint','--app','--yes','--skip-install'],
            destination('apps/web'))
    elif backend=='python':
        manual.append('Python '+p.get('backend_framework','undecided')+
                      ': crear apps/api con el generador oficial del framework y entorno virtual verificado. No se ejecuta pip automáticamente.')
    elif backend=='node' and p.get('backend_framework')=='nestjs':
        add('Backend NestJS',['npx','@nestjs/cli@latest','new',destination('apps/api'),'--skip-git','--skip-install'],
            destination('apps/api'))
    elif backend=='node':
        manual.append('Node.js '+p.get('backend_framework','undecided')+
                      ': configurar el generador oficial y su versión; no hay comando seguro preseleccionado.')
    elif backend=='java':
        manual.append('Java '+p.get('backend_framework','undecided')+
                      ': utilizar Spring Initializr / code.quarkus.io / Micronaut Launch con versiones verificadas; exportar a apps/api.')
    if frontend=='angular':
        manual.append('Angular: confirmar versión Node y Angular CLI; crear apps/web con ng new una vez aprobada la instalación del CLI.')
    if frontend in ('react','vue') and not (backend=='next' and frontend=='react'):
        folder=destination('apps/frontend' if backend=='next' else 'apps/web')
        template='react-ts' if frontend=='react' else 'vue-ts'
        add('Frontend '+frontend, ['npm','create','vite@latest',folder,'--','--template',template],folder)
    if mobile!='none':
        fw=p.get('mobile_framework')
        if fw=='flutter':
            platforms='android,ios' if mobile=='both' else mobile
            add('Flutter',['flutter','create','--platforms='+platforms,destination('apps/mobile')],destination('apps/mobile'))
        elif fw=='react-native':
            add('React Native (Expo)',['npx','create-expo-app@latest',destination('apps/mobile'),'--no-install'], destination('apps/mobile'))
            manual.append('Validar si se requiere Expo o React Native bare y configurar SDKs, permisos, variantes y signing.')
        else:
            if mobile in ('android','both'):
                manual.append('Android nativo: generar proyecto Android Studio en apps/android (Kotlin/Java del perfil).')
            if mobile in ('ios','both'):
                manual.append('iOS nativo: generar proyecto Xcode en apps/ios (requiere macOS y Xcode).')
    if layout=='singlerepo':
        manual=[note.replace('apps/api','raíz').replace('apps/web','raíz')
                .replace('apps/mobile','raíz').replace('apps/android','raíz').replace('apps/ios','raíz')
                for note in manual]
    return commands,manual


def plan(p:dict) -> str:
    cmds,manual=command_plans(p)
    text=['# Engineering Scaffold (generadores oficiales; ejecución opcional)','']
    for item in cmds:
        text.append('- '+item['label']+': '+ ' '.join(item['command']) + '  →  '+item['creates'])
    for note in manual:
        text.append('- MANUAL: '+note)
    if not cmds:
        text.append('- Este stack sólo tiene instrucciones manuales de scaffold.')
    text+=['','Cada comando puede acceder a Internet e instalar dependencias. '
           'Revisa versiones/SDK y los destinos antes de usar `apply`. '
           'Docker/CI/OTel requieren ajustes una vez generada la aplicación.']
    return '\n'.join(text)+'\n'


def _single_scaffold(p: dict, root: Path, item: dict, runner) -> int:
    """Genera aisladamente y vuelca a la raíz sólo tras verificar todos los conflictos."""
    name = re.sub(r'[^a-z0-9-]', '-', str(p.get('name','application')).lower()).strip('-') or 'application'
    with tempfile.TemporaryDirectory(prefix='aikya-scaffold-') as tmp:
        stage = Path(tmp)/name
        stage.mkdir()
        print('EJECUTANDO EN STAGING:', item['command'], flush=True)
        try:
            result=runner(item['command'],cwd=stage,check=False,timeout=600)
        except (OSError,subprocess.TimeoutExpired) as exc:
            print('Falló generador: '+str(exc),file=sys.stderr);return 1
        if result.returncode:
            print('Falló el generador: no se copiaron archivos del staging.',file=sys.stderr);return 1
        files=[]
        for base,dirs,names in os.walk(stage,followlinks=False):
            for dirname in dirs:
                if (Path(base)/dirname).is_symlink():
                    print('El scaffold contiene un enlace simbólico: operación cancelada.',file=sys.stderr);return 2
            for filename in names:
                original=Path(base)/filename
                if original.is_symlink() or not original.is_file():
                    print('Scaffold contiene un archivo no regular: operación cancelada.',file=sys.stderr);return 2
                rel=original.relative_to(stage)
                if rel.parts[0]=='.git':
                    continue
                files.append((original,rel))
        if not files:
            print('Generador no produjo archivos.',file=sys.stderr);return 1
        conflicts=[]
        for original,rel in files:
            dest=root/rel
            if dest.exists() and rel.as_posix()!='.gitignore':
                conflicts.append(str(rel))
            if any(part.is_symlink() for part in (dest,*dest.parents) if root in (part,*part.parents)):
                conflicts.append(str(rel)+' (enlace simbólico)')
        if conflicts:
            print('Conflictos en la raíz, no se copió ningún archivo: '+', '.join(conflicts[:20]),file=sys.stderr)
            return 2
        # La regla especial combina patrones de .gitignore sin eliminar los anteriores.
        for original,rel in files:
            dest=root/rel
            if rel.as_posix()=='.gitignore' and dest.exists():
                existing=dest.read_text(encoding='utf8').splitlines()
                incoming=original.read_text(encoding='utf8').splitlines()
                missing=[line for line in incoming if line not in existing]
                if missing:
                    with dest.open('a',encoding='utf8') as out:
                        out.write('\n# Añadido por scaffolding de Aikya\n'+'\n'.join(missing)+'\n')
                continue
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(original,dest)
    return 0


def sdd_approved(root: Path, profile: dict, spec_id=None, task_id=None) -> bool:
    """Require the selected specification and task; historical approvals do not count."""
    if profile.get("methodology", "standard") != "sdd": return True
    try:
        from aikya.workflows.sdd.engine import require_approved_task
        require_approved_task(root, spec_id, task_id)
        return True
    except (ImportError, ValueError, OSError, TypeError, KeyError):
        return False


def apply(p:dict, root:Path, assume_yes:bool=False, runner=subprocess.run, *, spec_id=None, task_id=None) -> int:
    cmds,manual=command_plans(p)
    root=root.resolve()
    if p.get('project_type','development')!='development':
        print('No se permiten generadores de aplicación en Infrastructure/DevOps.',file=sys.stderr)
        return 2
    if p.get('mode')!='new':
        print('No ejecutar scaffold sobre proyecto existente.',file=sys.stderr)
        return 2
    if not sdd_approved(root,p,spec_id,task_id):
        print('SDD requires an approved --spec-id and --task-id before scaffolding.',file=sys.stderr)
        return 2
    if not cmds:
        print(plan(p))
        return 0 if manual else 1
    single=p.get('repository_layout','monorepo')=='singlerepo'
    # Preflight completo antes de lanzar cualquier generador.
    for item in cmds:
        dest=(root/item['creates']).resolve()
        if not dest.is_relative_to(root):
            print('Ruta fuera del proyecto; abortado.',file=sys.stderr);return 2
        if not single and dest.exists():
            print(f'Destino ya existente: {dest}; no se sobrescribe ni ejecuta.',file=sys.stderr);return 2
        if not shutil.which(item['requires']):
            print('Falta herramienta '+item['requires'],file=sys.stderr);return 2
    detector_path=root/'aikya/scripts/harness/aikya_requirements.py'
    if not detector_path.exists():
        detector_path=root/'scripts/harness/aikya_requirements.py'
    if not detector_path.exists():
        detector_path=root/'.aikya/runtime/aikya_requirements.py'
    if not detector_path.exists():
        print('Falta detector de requisitos. Ejecuta /aikya-init.',file=sys.stderr);return 4
    import importlib.util
    spec=importlib.util.spec_from_file_location('aikya_requirements_local',detector_path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    report=mod.check(p,root)
    if not report['ready']:
        print('Requisitos pendientes: ejecuta /aikya-doctor.',file=sys.stderr)
        for check in report['checks']:
            if check['status']!='ok':
                print(f" - {check['tool']}: {check['status']}",file=sys.stderr)
        return 4
    print(plan(p))
    if not assume_yes and input('¿Ejecutar los generadores? [s/N]: ').strip().lower() not in ('s','si','sí','yes','y'):
        print('Cancelado.');return 0
    if single:
        if len(cmds)!=1:
            print('singlerepo sólo permite un generador. Selecciona monorepo.',file=sys.stderr);return 2
        result=_single_scaffold(p,root,cmds[0],runner)
        if result:return result
    else:
        (root/'apps').mkdir(exist_ok=True)
        for item in cmds:
            try:
                res=runner(item['command'],cwd=root,check=False,timeout=600)
            except (OSError,subprocess.TimeoutExpired) as exc:
                print('Fallo: '+str(exc),file=sys.stderr);return 1
            if res.returncode:
                print('Generador falló, revisa archivos parciales.',file=sys.stderr);return 1
    if manual:print('Pasos manuales pendientes: '+'; '.join(manual))
    print('Scaffolding completado. Verifica pruebas, checks de harness.json y documentación en aikya/docs/.')
    return 0


def main(argv=None):
    parser=argparse.ArgumentParser(description='Planificar o ejecutar generadores oficiales de apps')
    parser.add_argument('mode',choices=['plan','apply'])
    parser.add_argument('--yes',action='store_true',help='Confirmación explícita para ejecución desatendida; puede acceder a Internet')
    parser.add_argument('--spec-id')
    parser.add_argument('--task-id')
    args=parser.parse_args(argv)
    try:
        p=load_profile(ROOT)
        if args.mode=='plan':
            print(plan(p)); return 0
        return apply(p,ROOT,args.yes,spec_id=args.spec_id,task_id=args.task_id)
    except (OSError,ValueError,KeyboardInterrupt,EOFError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr)
        return 2

if __name__=='__main__':
    sys.exit(main())
