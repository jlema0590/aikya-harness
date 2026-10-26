#!/usr/bin/env python3
"""Aikya Skills support CLI. New-project interviews run inside Claude Code."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
# Dry-run and report-only must not leave bytecode in a project-local Aikya runtime.
sys.dont_write_bytecode = True
import aikya.installation.facade as installer
from aikya.installation.requirements import check, markdown


def resolved_answers(args, target:Path) -> Path:
    if args.answers:
        path=args.answers.expanduser().resolve()
    else:
        candidates=[target/'.aikya/answers.json',target/'.harness/project-profile.json']
        path=next((p for p in candidates if p.is_file()),candidates[0])
    if not path.is_file():
        raise ValueError(f'No technical profile was found at {path}; use /aikya-init for new projects, /aikya-analyze for existing repositories, or provide --answers.')
    return path


def main(argv=None):
    selected=sys.argv[1:] if argv is None else list(argv)
    if selected and selected[0]=='memory':
        from aikya.cli.memory import main as memory_main
        return memory_main(selected[1:])
    parser=argparse.ArgumentParser(description='Aikya Harness commands executed by Claude Code')
    parser.add_argument('command',choices=['probe','requirements','init','answers','status','analyze','feature','bugfix','implement','memory'])
    parser.add_argument('--target',type=Path,default=Path.cwd())
    parser.add_argument('--answers',type=Path)
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--strict',action='store_true',help='Fail with exit 4 if SDK requirements are incomplete')
    parser.add_argument('--external',choices=['skip','plan','install'],default='plan')
    parser.add_argument('--display-name')
    parser.add_argument('--scope',default='.')
    parser.add_argument('--focus',choices=['general','security','architecture','infrastructure','operations'],default='general')
    parser.add_argument('--docs-lang',choices=['en','es'],default=None,help='Aikya living documentation language')
    parser.add_argument('--methodology', choices=['odd', 'sdd', 'standard'], default=None)
    parser.add_argument('--session',default=__import__('os').environ.get('CLAUDE_SESSION_ID','local'))
    parser.add_argument('--execution-details',action='store_true')
    parser.add_argument('--refresh',action='store_true')
    parser.add_argument('--report-only',action='store_true')
    parser.add_argument('--approved',action='store_true',help='Explicit approval to create Aikya-owned files')
    parser.add_argument('--agent-loop',action='store_true',help='Explicit bounded execution for feature, bugfix or implement only')
    parser.add_argument('--loop-input',type=Path,help='Reviewed agent loop JSON, including scoped files, checks and budgets')
    parser.add_argument('--loop-run-id',help='Resume a durable loop without resetting limits')
    args=parser.parse_args(argv)
    target=args.target.expanduser().resolve()
    if args.agent_loop or args.command in ('feature','bugfix','implement'):
        if not args.agent_loop or args.command not in ('feature','bugfix','implement') or not args.loop_input or args.dry_run or args.report_only:
            parser.error('feature/bugfix/implement require --agent-loop and --loop-input; onboarding never starts a loop')
        from aikya.core.loop import run
        try:
            if args.loop_input.is_symlink() or not args.loop_input.is_file() or args.loop_input.stat().st_size>100_000:raise ValueError('Reviewed regular loop JSON required')
            raw=json.loads(args.loop_input.read_text())
            if raw.get('command')!='aikya-'+args.command:raise ValueError('Loop command does not match the requested command')
            result=run(target,raw,approved=args.approved,run_id=args.loop_run_id)
            print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['status']=='completed' else 4
        except (ValueError,OSError,TypeError,KeyError) as exc:
            print('ERROR: '+str(exc),file=sys.stderr);return 2
    lifecycle=None
    if args.command in ('init','analyze'):
        from aikya.middleware.lifecycle import Lifecycle
        lifecycle=Lifecycle(target,args.session,'aikya-'+args.command,preview=args.dry_run or args.report_only or (args.command=='analyze' and not args.approved),methodology=args.methodology)
    if args.command=='analyze':
        from aikya.discovery.analyze import execute
        try:
            result=execute(target,scope=args.scope,focus=args.focus,
                           approved=args.approved,refresh=args.refresh,
                           dry_run=args.dry_run,report_only=args.report_only,docs_lang=args.docs_lang,methodology=args.methodology,observer=lifecycle)
        except (ValueError,OSError,UnicodeError,TypeError) as exc:
            print('ERROR during analysis:',exc,file=sys.stderr)
            lifecycle.event('explore','failed',reason=str(exc));lifecycle.finish('failed',str(exc))
            return 2
        lifecycle.result(result,preview=args.dry_run or args.report_only)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result['status']=='READY' else 4
    if args.command=='probe':
        detected=installer.detect_project(target) if target.exists() else {'modules':[],'findings':['New directory']}
        print(json.dumps({'target':str(target),'detected':detected,
                          'existing_profile':installer.read_json_safe(target/'.harness/project-profile.json'),
                          'aikya_bootstrap':(target/'.aikya/bootstrap.json').is_file()},ensure_ascii=False,indent=2))
        return 0
    if args.command=='status':
        from aikya.core.state import read_active
        from aikya.middleware.metrics import read_metrics
        from aikya.middleware.statusline import render_status
        context={'root':str(target),'session_id':args.session}
        if args.execution_details:
            print(render_status(read_active(context) or {},read_metrics(context),width=180,detail=True));return 0
        print(json.dumps({'configured':(target/'.harness/project-profile.json').is_file(),
           'docs':(target/'aikya/docs/README.md').is_file(),
           'answers':(target/'.aikya/answers.json').is_file()},indent=2))
        return 0
    try:
        source=resolved_answers(args,target)
        raw=json.loads(source.read_text(encoding='utf8'))
        decisions=raw.get('decisions',raw)
        if args.command=='init' and decisions.get('mode')=='existing':
            message='/aikya-init is only for new projects; use /aikya-analyze'
            print('ERROR: '+message,file=sys.stderr)
            lifecycle.event('explore','blocked',reason=message);lifecycle.finish('blocked',message);return 2
        if args.command=='init' and args.methodology is None and decisions.get('methodology') is None:
            lifecycle.done('explore','Answers parsed; methodology selection is absent')
            lifecycle.event('plan','waiting',reason='Choose ODD or SDD before creating project files')
            print(json.dumps({'status':'NEEDS_METHODOLOGY','writes':False,'methodology_options':['odd','sdd'],'recommended_methodology':'odd'}))
            return 4
        profile=installer.validated({**decisions,**({'methodology':args.methodology} if args.methodology else {})},target)
    except (ValueError,OSError,UnicodeError,TypeError) as exc:
        print('ERROR parsing answers:',exc,file=sys.stderr)
        if lifecycle:lifecycle.event('explore','failed',reason=str(exc));lifecycle.finish('failed',str(exc))
        return 2
    if args.command=='init' and profile['mode']!='new':
        print('ERROR: /aikya-init is only for new projects. Use /aikya-analyze for existing repositories; nothing was written.',file=sys.stderr)
        return 2
    if args.command=='answers' and profile['mode']=='existing':
        print('NOTICE: legacy declarative profile; use /aikya-analyze for automatic existing-repository discovery.',file=sys.stderr)
        # Compatibility shim: existing profiles remain valid but no user IaC, CI or Docker files change.
        detected=installer.detect_project(target)
        try:
            actions=installer.install(target,profile,detected,dry_run=args.dry_run,adopt_existing=True,docs_lang=args.docs_lang)
        except (ValueError,OSError,UnicodeError) as exc:
            print('ERROR during adoption:',exc,file=sys.stderr)
            return 2
        print(json.dumps({'mode':'existing','dry_run':args.dry_run,'actions':actions},
                         ensure_ascii=False,indent=2))
        return 0
    report=check(profile,target)
    print('\n=== AIKYA TOOLCHAIN REQUIREMENTS ===')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if args.command=='requirements':
        return 4 if args.strict and not report['ready'] else 0
    if args.strict and not report['ready']:
        print('REQUIREMENTS PENDING: request developer approval before updating SDKs.',file=sys.stderr)
        if lifecycle:
            lifecycle.done('explore','Toolchain availability inspected')
            lifecycle.event('plan','blocked',reason='Strict toolchain requirements are incomplete')
            lifecycle.finish('blocked','Strict toolchain requirements are incomplete')
        return 4
    # run through current process (same interpreter), never auto-install SDKs.
    flags=['--target',str(target),'--answers',str(source),'--external',args.external]
    if args.methodology:flags+=['--methodology',args.methodology]
    if args.dry_run: flags.append('--dry-run')
    if args.display_name: flags+=['--display-name',args.display_name]
    if args.docs_lang: flags+=['--docs-lang',args.docs_lang]
    if (target/'.aikya/bootstrap.json').exists() or (target/'.aikya/answers.json').exists(): flags.append('--allow-bootstrap')
    if lifecycle:
        lifecycle.done('explore','New-project answers and toolchain availability inspected')
        lifecycle.done('plan','Explicit methodology and installation scope confirmed')
        if not args.dry_run:lifecycle.event('implement','running','Creating approved Aikya harness files')
    result=installer.main(flags)
    if lifecycle:
        if result==0:
            if args.dry_run:lifecycle.done('validate','Installer preflight completed without writes',True);lifecycle.finish('completed')
            else:lifecycle.done('implement','Installer returned successfully');lifecycle.verify_install()
        else:lifecycle.event('implement' if not args.dry_run else 'validate','failed',reason='Installer returned exit '+str(result));lifecycle.finish('failed','Installer failed')
    if result==0 and not args.dry_run:
        from aikya.documentation.layout import append_section
        try:
            locale = __import__('aikya.documentation.language',fromlist=['*']).resolve(target, args.docs_lang)
            append_section(target, 'overview.md', 'Toolchain diagnostics' if locale == 'en' else 'Diagnóstico de herramientas', markdown(report, locale))
        except ValueError as exc:
            print('NOTICE: customized overview preserved: '+str(exc), file=sys.stderr)
        print('\nAikya installed. Resolve outstanding SDK requirements before running project generators.')
    return result

if __name__=='__main__':sys.exit(main())
