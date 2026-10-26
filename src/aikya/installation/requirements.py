#!/usr/bin/env python3
"""Read-only LOCAL Aikya toolchain diagnostics. Never installs SDKs."""
from __future__ import annotations
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from aikya.discovery.infrastructure import capabilities

DOCS = {
    'python3': 'https://www.python.org/downloads/',
    'git': 'https://git-scm.com/downloads',
    'java': 'https://adoptium.net/',
    'javac': 'https://adoptium.net/',
    'dotnet': 'https://dotnet.microsoft.com/download',
    'node': 'https://nodejs.org/en/download',
    'npm': 'https://nodejs.org/en/download',
    'pnpm': 'https://pnpm.io/installation',
    'yarn': 'https://yarnpkg.com/getting-started/install',
    'bun': 'https://bun.sh/docs/installation',
    'flutter': 'https://docs.flutter.dev/get-started/install',
    'xcodebuild': 'https://developer.apple.com/xcode/',
    'adb': 'https://developer.android.com/studio',
    'sdkmanager': 'https://developer.android.com/tools/sdkmanager',
    'android-sdk': 'https://developer.android.com/studio',
    'terraform':'https://developer.hashicorp.com/terraform/install',
    'opentofu':'https://opentofu.org/docs/intro/install/',
    'ansible':'https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html',
    'docker':'https://docs.docker.com/get-docker/',
    'docker-compose':'https://docs.docker.com/compose/install/',
    'kubectl':'https://kubernetes.io/docs/tasks/tools/',
    'helm':'https://helm.sh/docs/intro/install/',
    'kustomize':'https://kubectl.docs.kubernetes.io/installation/kustomize/',
}


def expected_versions(profile: dict[str, Any], target: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    notes = str(profile.get('runtime_versions') or '')
    for key, expression in {'java':r'\b(?:java|jdk)\s*(?:sdk\s*)?(\d+(?:\.\d+)*)',
                            'dotnet':r'\b(?:\.net|dotnet)\s*(?:sdk\s*)?(\d+(?:\.\d+)*)',
                            'node':r'\b(?:node\.?js|node)\s*(?:v\s*)?(\d+(?:\.\d+)*)',
                            'python3':r'\bpython\s*(?:v\s*)?(\d+(?:\.\d+)*)'}.items():
        match = re.search(expression, notes, re.IGNORECASE)
        if match: result[key] = match.group(1)
    nvmrc = target / '.nvmrc'
    if 'node' not in result and nvmrc.is_file():
        match = re.search(r'v?(\d+(?:\.\d+)*)', nvmrc.read_text(encoding='utf8').strip())
        if match: result['node'] = match.group(1)
    globaljson = target / 'global.json'
    if 'dotnet' not in result and globaljson.is_file():
        try:
            value = json.loads(globaljson.read_text(encoding='utf8'))
            sdk = value.get('sdk', {}).get('version', '')
            if re.match(r'^\d+\.\d+', sdk): result['dotnet'] = sdk
        except (ValueError, OSError, TypeError, AttributeError): pass
    javaver = target / '.java-version'
    if 'java' not in result and javaver.is_file():
        match = re.search(r'\b(\d+(?:\.\d+)*)', javaver.read_text(encoding='utf8'))
        if match: result['java'] = match.group(1)
    return result


def required_tools(profile: dict[str, Any]) -> list[str]:
    tools = ['python3', 'git']
    backend, frontend, mobile = profile.get('backend'), profile.get('frontend'), profile.get('mobile')
    framework = profile.get('mobile_framework')
    if backend == 'java': tools += ['java', 'javac']
    if backend == 'dotnet': tools += ['dotnet']
    if backend in ('node', 'next') or frontend in ('react', 'vue', 'angular') or framework == 'react-native':
        tools += ['node', profile.get('package_manager') if profile.get('package_manager') in ('pnpm','yarn','bun') else 'npm']
    if mobile not in ('none', None):
        if framework == 'flutter': tools += ['flutter']
        if framework == 'native' and mobile in ('android', 'both'):
            tools += ['java', 'javac', 'android-sdk', 'adb']
        if framework in ('flutter','react-native') and mobile in ('android','both'): tools += ['android-sdk', 'adb']
        if mobile in ('ios','both'): tools += ['xcodebuild']
    tools += capabilities(profile)
    return list(dict.fromkeys(tools))


def command_version(tool: str) -> tuple[str | None, str | None]:
    if tool == 'android-sdk':
        candidates=[Path(os.environ[key]).expanduser() for key in ('ANDROID_HOME','ANDROID_SDK_ROOT') if os.environ.get(key)]
        candidates += [Path.home()/'Android/Sdk',Path.home()/'Library/Android/sdk']
        for folder in candidates:
            if (folder/'platforms').is_dir() and any((folder/'platforms').glob('android-*')) and (folder/'build-tools').is_dir():
                return f'SDK instalado en {folder}', None
        return None, 'Android SDK Platform + Build Tools no detectados (ANDROID_HOME/ANDROID_SDK_ROOT)'
    if tool == 'python3':
        return f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}', None
    path = shutil.which('docker' if tool=='docker-compose' else 'tofu' if tool=='opentofu' else tool)
    if not path:
        return None, 'No encontrado en PATH'
    args = {'java':['-version'], 'javac':['-version'], 'dotnet':['--list-sdks'],
            'docker-compose':['compose','version','--short'],
            'kubectl':['version','--client=true'],
            'xcodebuild':['-version'], 'adb':['version'], 'sdkmanager':['--version']}
    try:
        r = subprocess.run([path, *args.get(tool,['--version'])], capture_output=True, text=True, timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f'No se pudo ejecutar: {type(exc).__name__}'
    output = ((r.stdout or '') + '\n' + (r.stderr or '')).strip()
    if r.returncode and not output:
        return None, f'Command failed (exit {r.returncode})'
    if tool == 'dotnet':
        versions=re.findall(r'(?m)^(\d+\.\d+\.\d+)\s+\[', output)
        if versions:
            ordered=sorted(versions,key=lambda ver:tuple(int(n) for n in ver.split('.')), reverse=True)
            return ','.join(ordered), None
    # Version formats vary; use word boundaries after a numeric v-prefixed version
    # no coincide (v25.9.0 se interpretaba 9.0). Aplicar un parser robusto.
    if tool in ('node','npm','pnpm','yarn','bun','docker-compose'):
        expression = r'(?<![\d.])v?(\d+(?:\.\d+){0,3})\b'
    elif tool == 'java':
        expression = r'(?:version\s+")?(\d+(?:\.\d+){0,3})(?:["\s]|$)'
    else:
        expression = r'(?<![\d.])v?(\d+(?:\.\d+){0,3})\b'
    match = re.search(expression, output, re.IGNORECASE)
    if match:
        return match.group(1), None
    return None, 'Cannot parse the version reported by '+tool


def check(profile: dict[str, Any], target: Path) -> dict[str, Any]:
    expected = expected_versions(profile,target)
    results=[]
    for tool in required_tools(profile):
        wanted=expected.get('java' if tool=='javac' else tool)
        if tool == 'xcodebuild' and platform.system() != 'Darwin':
            status, actual, detail = 'unsupported_host', None, 'iOS nativo requiere macOS y Xcode para compilar'
        elif tool == 'python3':
            actual, detail = command_version(tool)
            status = 'ok' if sys.version_info >= (3,9) else 'version_mismatch'
            minimum = expected.get('python3')
            wanted = minimum or '3.9+'
            if minimum:
                wanted_parts = tuple(int(n) for n in minimum.split('.'))
                actual_parts = (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
                if actual_parts[:len(wanted_parts)] < wanted_parts or actual_parts[0] != wanted_parts[0]:
                    status = 'version_mismatch'
        else:
            actual,detail=command_version(tool)
            status='ok' if actual is not None else 'missing'
            if actual and wanted:
                if tool == 'dotnet' and ',' in actual:
                    requested_major=re.match(r'^(\d+)',wanted)
                    versions=actual.split(',')
                    preferred=next((v for v in versions if v.split('.')[0]==requested_major.group(1)), versions[0]) if requested_major else versions[0]
                    actual=preferred
                got = re.match(r'^\d+(?:\.\d+)*',actual)
                required = re.match(r'^\d+(?:\.\d+)*',wanted)
                if got and required:
                    got_parts=[int(n) for n in got.group().split('.')]
                    req_parts=[int(n) for n in required.group().split('.')]
                    # Exact version supplied, including minor/patch: requested minimum,
                    # preserving major-version comparisons when only the major is specified.
                    if got_parts[0] != req_parts[0] or (len(req_parts)>1 and tuple((got_parts+[0]*4)[:len(req_parts)]) < tuple(req_parts)):
                        status='version_mismatch'
                else:
                    status='unverified_version'
        results.append({'tool':tool,'status':status,'installed':actual,'expected':wanted,'detail':detail or '',
                        'official_url':DOCS.get(tool,'')})
    return {'schema_version':1,'project':str(target),'platform':platform.system(),
            'ready':all(x['status']=='ok' for x in results), 'checks':results,
            'note':'Non-destructive diagnosis. No SDKs or dependencies are installed. Framework, AGP and Xcode compatibility requires separate verification.'}


def markdown(report: dict[str, Any], language: str = "en") -> str:
    from aikya.documentation.layout import stamp
    from aikya.documentation.language import validate as validate_docs_language
    if validate_docs_language(language) == "en":
        lines = ["<!-- GENERATED BY AIKYA-HARNESS -->", "# Toolchain requirements", "",
                 "Local diagnosis only. Installed tools do not prove application builds or "
                 "framework compatibility.", "",
                 "| Tool | Status | Installed | Required | Official guide |",
                 "|---|---|---|---|---|"]
        for item in report["checks"]:
            lines.append("| " + " | ".join([str(item["tool"]), str(item["status"]),
                         str(item["installed"] or "—"),
                         str(item["expected"] or "Not pinned"),
                         str(item["official_url"])]) + " |")
        lines += ["", "Result: **" + ("Toolchain detected" if report["ready"] else "Requirements pending") + "**.", "",
                  "Request explicit authorization before installing or upgrading SDKs.",
                  "Run /aikya-doctor again after correcting the toolchain. Never claim "
                  "builds or tests passed because an SDK was detected.", ""]
        return stamp("\n".join(lines))
    lines=['<!-- GENERATED BY AIKYA-HARNESS -->','# Requisitos del entorno','',
           'Diagnóstico local de herramientas tras la entrevista. **No sustituye un build real ni valida compatibilidad entre frameworks.**','',
           '| Herramienta | Estado | Instalada | Solicitada | Guía oficial |',
           '|---|---|---|---|---|']
    for item in report['checks']:
        lines.append('| '+ ' | '.join([str(item['tool']),str(item['status']),str(item['installed'] or '—'),
          str(item['expected'] or 'sin fijar'),str(item['official_url'])])+' |')
    lines += ['',f"Resultado: **{'Toolchain detectado' if report['ready'] else 'Requisitos pendientes'}**.",
              '', 'Ante requisitos ausentes o incompatibles, solicita aprobación para instalar/actualizar desde las fuentes oficiales.',
              'Repite `/aikya-doctor` después de corregir el entorno. No marques builds o pruebas como superados por detectar SDKs.','']
    return stamp('\n'.join(lines))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Read-only SDK diagnostics')
    parser.add_argument('--target', type=Path, default=Path.cwd())
    parser.add_argument('--answers', type=Path)
    parser.add_argument('--strict', action='store_true')
    args=parser.parse_args()
    target=args.target.expanduser().resolve()
    source=args.answers or target/'.harness/project-profile.json'
    raw=json.loads(source.read_text(encoding='utf8'))
    report=check(raw.get('decisions',raw),target)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if args.strict and not report['ready']: sys.exit(4)
