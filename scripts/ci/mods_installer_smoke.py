"""Exercise final Harness/Mods assets with real Claude in disposable configurations."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def check(assets, mods_assets):
    if not shutil.which('claude'):
        raise ValueError('Real native Claude CLI is required for this acceptance check')
    wheel=next(assets.glob('aikya_harness-*-py3-none-any.whl'))
    version=wheel.name.removeprefix('aikya_harness-').removesuffix('-py3-none-any.whl')
    mods_version=json.loads((mods_assets/'release.json').read_text())['version'].removeprefix('v')
    results=[]
    with tempfile.TemporaryDirectory(prefix='aikya-mods-smoke-') as temporary:
        base=Path(temporary).resolve();offline=base/'assets';offline.mkdir()
        for name in ('SHA256SUMS','aikya-bootstrap.pyz','install.sh','install.ps1',wheel.name):
            shutil.copyfile(assets/name,offline/name)
        (offline/'mods').mkdir()
        for name in ('SHA256SUMS','release.json','aikya-mods-v'+mods_version+'.zip'):
            shutil.copyfile(mods_assets/name,offline/'mods'/name)
        cases=[('global','recommended'),('project','recommended'),('global','all'),('project','all'),('global','none'),('project','none')]
        for index,(scope,selection) in enumerate(cases):
            case=base/('case-'+str(index));case.mkdir();home=case/'home';home.mkdir();project=case/"team's project";project.mkdir()
            env={**os.environ,'HOME':str(home),'USERPROFILE':str(home),'AIKYA_INSTALL_ROOT':str(case/'app'),
                 'AIKYA_MODS_HOME':str(case/'mods'),'CLAUDE_CONFIG_DIR':str(case/'claude'),
                 'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC':'1','DISABLE_TELEMETRY':'1'}
            env.pop('CLAUDE_PROJECT_DIR',None)
            target=['--target',str(project)] if scope=='project' else []
            options=['--scope',scope,*target,'--offline-dir',str(offline),'--version',version,
                     '--mods-version',mods_version,'--no-path']
            def run(argv):
                result=subprocess.run([str(x) for x in argv],env=env,cwd=project,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=240)
                if result.returncode:raise ValueError(repr(argv)+'\n'+result.stdout[-2000:]+result.stderr[-3000:])
                return result.stdout
            if os.name=='nt':
                entry=['powershell','-NoProfile','-File',offline/'install.ps1','-Scope',scope,'-OfflineDir',offline,
                       '-Version',version,'-ModsVersion',mods_version,'-Mods',selection,'-NoPath','-Python',sys.executable]
                if scope=='project':entry+=['-Target',project]
            else:
                entry=['/bin/sh',offline/'install.sh',*options,'--mods',selection,'--python',sys.executable]
            run(entry)
            expected=[] if selection=='none' else ['aikya-flow','aikya-usage']
            if selection=='all':expected+=['aikya-boxbot']
            inventory=json.loads(run(['claude','plugin','list','--json']))
            assert sorted(p['id'].split('@')[0] for p in inventory)==sorted(expected)
            manager=[sys.executable,'-I','-B',offline/'aikya-bootstrap.pyz']
            # No new selection: update must preserve registered IDs, including none.
            run([*manager,'update',*options])
            again=json.loads(run(['claude','plugin','list','--json']))
            assert sorted(p['id'] for p in again)==sorted(p['id'] for p in inventory)
            run([*manager,'doctor'])
            run([*manager,'uninstall','--scope',scope,*target])
            assert json.loads(run(['claude','plugin','list','--json']))==[]
            assert not (case/'app/current.json').exists()
            results.append({'scope':scope,'selection':selection,'install':'passed','update':'passed','doctor':'passed','uninstall':'passed'})
    return {'platform':sys.platform,'version':version,'mods_version':mods_version,'live_model':False,'cases':results}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--mods-assets',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    report=check(args.assets.resolve(),args.mods_assets.resolve())
    if args.output:args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
