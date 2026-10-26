"""Explicit synthetic executor: edits a fixture and reports protocol events."""
import json,os,subprocess,sys,time,uuid
from pathlib import Path
request=json.loads(sys.stdin.readline());mode=os.environ.get('AIKYA_FIXTURE_MODE','write')
def send(value):print(json.dumps(value),flush=True)
if mode=='grandchild':
 marker=str(Path(request['root'])/'child-survived')
 subprocess.Popen([sys.executable,'-c',"import time;from pathlib import Path;time.sleep(.8);Path("+repr(marker)+").write_text('unexpected')"])
 time.sleep(60)
if mode=='flood':print('x'*200000,flush=True);raise SystemExit(0)
if mode=='hang':time.sleep(60)
if mode=='crash':raise SystemExit(9)
if mode=='malformed':print('not json',flush=True);raise SystemExit(0)
if request['phase']=='extract' and mode.startswith('extract'):
 candidate={'kind':'project','text':'Keep value lookup stable.','source':'src/value.py','ttl_days':30}
 if mode=='extract_escape':candidate['source']='../outside.txt'
 if mode=='extract_stale':(Path(request['root'])/'src/value.py').write_text('VALUE = 9\n')
 send({'type':'result','id':uuid.uuid4().hex,'session_id':uuid.uuid4().hex,'cost_usd':0.001,'model':None,'output':{'candidates':[candidate]*(4 if mode=='extract_many' else 1)}})
 raise SystemExit(0)
if request['phase']=='implement' and mode in ('write','stale','pending','escape','slow_write'):
 path='src/value.py' if mode!='escape' else '../outside.txt';ident=uuid.uuid4().hex
 send({'type':'effect_intent','id':ident,'tool':'Write','path':path})
 ack=json.loads(sys.stdin.readline())
 if ack.get('ack')!=ident:raise SystemExit(4)
 if mode=='pending':raise SystemExit(9)
 if mode=='slow_write':time.sleep(.4)
 (Path(request['root'])/path).write_text('VALUE = 1\n')
 send({'type':'effect_result','id':ident})
if request['phase']=='review' and mode=='stale':(Path(request['root'])/'src/value.py').write_text('VALUE = 2\n')
send({'type':'result','id':uuid.uuid4().hex,'session_id':request.get('session_id') or uuid.uuid4().hex,'cost_usd':None if mode=='unknown_usage' else 0.001,'model':None,'output':{'status':'done','approved':mode!='reject'}})
