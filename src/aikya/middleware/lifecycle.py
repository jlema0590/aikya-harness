"""Local CLI lifecycle. Evidence describes performed checks, never model judgement."""
from __future__ import annotations
import json,os,sys
from pathlib import Path
import aikya.core.state as state
from aikya.middleware.observer import project_method
class Lifecycle:
    def __init__(self,root,session,command,preview=False,methodology=None):
        self.context={'root':str(root),'session_id':session};self.enabled=True;self.generations={}
        try:
            method=methodology or project_method(root)
            active=state.attach_cli(self.context,command,method,preview) or state.start_run(self.context,command,methodology=method,preview=preview)
            self.context['run_id']=active['run_id'];self.event('explore','running','Inspecting the requested project scope')
        except (ValueError,OSError,TypeError):self.enabled=False
    def event(self,phase,status,activity='',reason='',evidence=None,candidate_generation=None):
        if not self.enabled:return
        try:
            value=state.record_event(self.context,{'candidate_generation':candidate_generation,'phase':phase,'status':status,'activity':activity,'reason':reason,'source':'local-python','actor_id':'local-python','evidence':evidence or []})
            if status=='running':self.generations[phase]=value.get('candidate_generation',0)
        except (ValueError,OSError,TypeError) as exc:
            self.enabled=False;print('NOTICE: execution metadata unavailable: '+str(exc),file=sys.stderr)
    def done(self,phase,check,inspection=False):
        kind='inspection' if inspection or phase in ('validate','security') else 'observation'
        generation=self.generations.get(phase)
        if generation is None and self.enabled:generation=state.read_snapshot(self.context).get('candidate_generation',0)
        self.event(phase,'completed',candidate_generation=generation if phase in ('validate','security','review') else None,evidence=[{'kind':kind,'check':check,'result':'passed' if kind=='inspection' else 'recorded'}])
    def finish(self,status,reason=''):
        if not self.enabled:return
        try:state.finish_run(self.context,status,reason)
        except (ValueError,OSError,TypeError) as exc:print('NOTICE: execution remains incomplete: '+str(exc),file=sys.stderr)
    def result(self,result,preview=False):
        self.done('explore','Project discovery/profile validation completed')
        status=result.get('status')
        if status=='NEEDS_METHODOLOGY' or (result.get('approval_required') and not preview):
            self.event('plan','waiting',reason='Choose ODD or SDD' if status=='NEEDS_METHODOLOGY' else 'Awaiting approval of the file plan');return
        if status!='READY':
            self.event('plan','blocked',reason='Analysis requires resolution: '+str(status));self.finish('blocked','Analysis is not ready');return
        self.done('plan','Requested methodology and file plan resolved')
        if result.get('writes'):
            self.done('implement','Approved Aikya harness installation returned successfully')
            self.verify_install()
        else:
            self.done('validate','Read-only discovery and file plan were generated',True);self.finish('completed')
    def verify_install(self):
        root=Path(self.context['root'])
        try:
            self.event('validate','running','Checking installed profile and runtime')
            profile=json.loads((root/'.harness/project-profile.json').read_text())
            from aikya.workflows.methodology import normalize_methodology
            normalize_methodology(profile['decisions'].get('methodology'))
            for name in ('methodology.py','execution_state.py','odd_engine.py','aikya_statusline.py'):
                if not (root/'aikya/scripts/harness'/name).is_file():raise ValueError('Missing installed runtime: '+name)
            self.done('validate','Installed profile parses and required execution/ODD modules exist',True)
            self.event('security','running','Checking managed paths and installed permission policy')
            from aikya.installation.migrations import managed_path_conflicts
            if managed_path_conflicts(root):raise ValueError('Managed path symlink conflict')
            config=json.loads((root/'.claude/settings.json').read_text())
            deny=config.get('permissions',{}).get('deny',[])
            if not isinstance(deny,list) or 'Read(./.env)' not in deny:raise ValueError('Custom settings require permission-policy review')
            self.done('security','Managed paths contain no symlinks; installed policy denies direct .env reads. Scope: bootstrap configuration only',True)
            self.finish('completed')
        except (ValueError,OSError,TypeError,KeyError) as exc:
            current=state.read_snapshot(self.context) if self.enabled else None
            phase=current.get('phase','validate') if current else 'validate'
            self.event(phase,'blocked',reason=str(exc));self.finish('blocked','Installed configuration requires review')
