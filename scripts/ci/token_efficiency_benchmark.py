"""Deterministic offline efficiency fixtures; no model requests or private projects."""
import argparse
import contextlib
import io
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
from aikya.quality.efficiency import command_coverage
from aikya.code_index.policy import configure, CODE_SUFFIXES
from aikya.code_index.parsers.registry import parse_file
from aikya.context.prepare import prepare_context

ROOT=Path(__file__).resolve().parents[2]


def benchmark():
    languages={}
    fixtures=ROOT/'tests/fixtures/language-coverage'
    manifest=json.loads((fixtures/'manifest.json').read_text())
    if set(manifest)!=set(CODE_SUFFIXES):raise ValueError('Missing extension fixture')
    for suffix,row in manifest.items():
        value=parse_file(row['file'],(fixtures/row['file']).read_bytes())
        languages[suffix]={'status':value.status,'parser':value.parser_id,'symbols':len(value.symbols),
                           'application_build':'not_run','reason':'Syntax/inventory test only; application toolchains not invoked'}
    commands=command_coverage()
    for name,row in commands.items():
        path=ROOT/'src/aikya/resources/commands'/name/'SKILL.md'
        text=path.read_text();row.update(mode='offline_instruction_contract',instruction_chars=len(text),
                                       instruction_proxy_tokens=round(len(text)/3.5),proxy_not_tokenizer=True)
    scenarios=[]
    with tempfile.TemporaryDirectory(prefix='aikya-efficiency-') as temporary:
        root=Path(temporary).resolve();configure(root,approved=True)
        dart=root/'login.dart'
        dart.write_text('class Login {\n  bool signIn(String user) => user.isNotEmpty;\n'+
                        ''.join('  int helper'+str(n)+'() => '+str(n)+';\n' for n in range(30))+'}\n')
        auth=root/'authentication.py'
        auth.write_text('class Authentication:\n    def authenticate(self): return False\n'+
                        ''.join('    def helper_'+str(n)+'(self): return '+str(n)+'\n' for n in range(30)))
        from aikya.code_index.query import query as legacy_query
        from aikya.routing.router import route
        for name,path,query in (('small_mobile_change','login.dart','change signIn'),
                                ('authentication_change','authentication.py','fix authenticate'),
                                ('external_edit','login.dart','change signIn')):
            if name=='external_edit':dart.write_text(dart.read_text().replace('user.isNotEmpty','user.length > 2'))
            baseline=asdict(legacy_query(root,'',allowed_files=[path]))
            baseline_chars=len(json.dumps(baseline,ensure_ascii=False))
            packet=prepare_context(root,query,paths=[path])
            chars=len(json.dumps(packet,ensure_ascii=False))
            expected='authenticate' if name=='authentication_change' else 'signIn'
            functional=bool(packet['context']) and expected in json.dumps(packet['context'])
            if name=='external_edit':functional= functional and 'user.length > 2' in json.dumps(packet['context'])
            risk=route('fix authentication' if name=='authentication_change' else 'fix label')['independent_review_required']
            scenarios.append({'name':name,'fixture':'synthetic scoped source retrieval; not full AI workflow',
                              'baseline_kind':'legacy query JSON including matches/context on the same allowed file',
                              'baseline_chars':baseline_chars,'candidate_chars':chars,
                              'context_reduction_pct':round((1-chars/baseline_chars)*100,2),
                              'within_packet_budget':chars<=6000,'functional':functional,
                              'requires_security':risk,'model_requests':None,'tokens':None})
        existing=root/'existing';existing.mkdir();(existing/'pom.xml').write_text('<project/>')
        from aikya.cli.main import main as cli
        sizes=[];codes=[]
        for summary in (False,True):
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                code=cli(['analyze','--target',str(existing),'--dry-run','--methodology','odd',*(['--summary'] if summary else [])])
            sizes.append(len(output.getvalue()));codes.append(code)
        scenarios.insert(0,{'name':'analyze','fixture':'native Analyze dry-run on identical synthetic Maven repository',
                           'baseline_kind':'full native response versus --summary', 'baseline_chars':sizes[0],
                           'candidate_chars':sizes[1],'context_reduction_pct':round((1-sizes[1]/sizes[0])*100,2),
                           'within_packet_budget':sizes[1]<=2000,'functional':codes[0]==codes[1],
                           'requires_security':False,'model_requests':None,'tokens':None})
    from aikya.installation.profile import validated
    from aikya.catalogs.engineering import discover
    workflows=[]
    for case in json.loads((fixtures/'workflows.json').read_text()):
        profile=validated(case['input'],ROOT)
        selected=discover(ROOT,profile,case.get('modules',[]))
        workflows.append({'name':case['name'],'status':'passed' if set(case['agents'])<=set(selected['agents']) else 'failed', 'methodology':profile['methodology'],'mode':profile['mode'],'application_build':'not_run', 'reason':'Validated profile and specialist selection only'})
    return {'schema':1,'mode':'offline deterministic fixtures','live_model_execution':False,
            'quota_savings':None,'real_token_savings':None,'commands':commands,'command_count':len(commands),
            'languages':languages,'workflows':workflows,'scenarios':scenarios,
            'valid':all(w['status']=='passed' for w in workflows) and all(s['within_packet_budget'] and s['functional'] for s in scenarios) and all(v['status'] in ('indexed','file_only') for v in languages.values()),
            'note':'Compare live model cost separately with equivalent accepted task/model/effort/cache and a reviewed budget.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    args=parser.parse_args();value=benchmark()
    if args.output:args.output.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({'valid':value['valid'],'commands':value['command_count'],'extensions':len(value['languages']),'live_model_execution':False}))
    return 0 if value['valid'] else 1

if __name__=='__main__':raise SystemExit(main())
