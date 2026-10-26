"""Best-effort validation metadata from actual configured local process checks."""
from __future__ import annotations
import os,uuid
import aikya.core.state as state
class CheckEvents:
    def __init__(self,root):
        self.context={'root':str(root),'session_id':os.environ.get('CLAUDE_SESSION_ID','local')};self.enabled=False;self.generation=None;self.actor='local-python:'+uuid.uuid4().hex
        try:
            active=state.read_active(self.context)
            if active and active['status'] not in state.TERMINAL:
                self.context['run_id']=active['run_id'];self.generation=active.get('candidate_generation',0);self.enabled=True;self.record('running')
        except (ValueError,OSError,TypeError,KeyError):pass
        self.evidence=[]
    def process(self,name,code):
        self.evidence.append({'kind':'process','check':name[:180],'exit_code':code})
    def record(self,status,reason=''):
        if not self.enabled:return
        try:state.record_event(self.context,{'phase':'validate','status':status,'reason':reason,'activity':'Running configured quality checks','candidate_generation':self.generation,'actor_id':self.actor,'source':'quality-runner','evidence':getattr(self,'evidence',[])[:40]})
        except (ValueError,OSError,TypeError,KeyError):self.enabled=False
    def finish(self,failures):
        if failures:self.record('failed','Configured checks failed or required checks are unavailable')
        elif not self.evidence:self.record('blocked','No executable checks were available')
        elif len(self.evidence)>40:self.record('blocked','More than 40 checks; record scoped evidence explicitly')
        else:self.record('completed')
