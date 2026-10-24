"""Provider limits, live context and recorded tokens are different quantities."""
import importlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
class RuntimeMetricsTests(unittest.TestCase):
 def mod(self):
  self.assertIsNotNone(importlib.util.find_spec('aikya.middleware.metrics'),'Missing runtime metrics adapter');return importlib.import_module('aikya.middleware.metrics')
 def test_missing_zero_expired_and_invalid_values_do_not_become_invented_usage(self):
  m=self.mod();raw={'model':{'id':'actual-model'},'context_window':{'used_percentage':25,'total_input_tokens':200},'rate_limits':{'five_hour':{'used_percentage':0,'resets_at':120},'seven_day':{'used_percentage':40,'resets_at':99}}}
  out=m.normalize_runtime_payload(raw,now=100)
  self.assertEqual('actual-model',out['model']);self.assertEqual(25,out['context_pct']);self.assertEqual(0,out['account_five_hour_pct']);self.assertIsNone(out['account_seven_day_pct']);self.assertIsNone(out['session_tokens'])
  self.assertIsNone(m.normalize_runtime_payload({},now=100)['context_pct'])
  self.assertIsNone(m.normalize_runtime_payload({'context_window':{'used_percentage':True}},now=100)['context_pct'])
  self.assertIsNone(m.normalize_runtime_payload({'context_window':{'used_percentage':float('nan')}},now=100)['context_pct'])
 def test_observed_model_is_not_inferred_from_policy_or_another_actor(self):
  m=self.mod();self.assertEqual({'configured':'inherit','observed':None,'source':'unavailable'},m.resolve_actor_model('inherit',None))
  self.assertEqual('resolved-child',m.resolve_actor_model('opus','resolved-child')['observed'])
 def test_usage_filter_deduplicates_streaming_and_reports_missing_timestamps(self):
  m=self.mod()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'session.jsonl'
   def event(ident,n,stamp='2026-10-23T10:00:00Z',session='s1'):
    return {'timestamp':stamp,'sessionId':session,'message':{'id':ident,'role':'assistant','model':'actual-model','usage':{'input_tokens':10,'output_tokens':n}}}
   records=[event('a',2),event('a',5),event('old',100,'2026-10-01T10:00:00Z'),event('b',7,session='s2'),event('undated',3,None)]
   p.write_text('\n'.join(json.dumps(e) for e in records)+'\n')
   out=m.aggregate_usage([p],start_utc='2026-10-23T00:00:00Z',end_utc='2026-10-24T00:00:00Z',session_id='s1')
   self.assertEqual(10,out['totals']['input_tokens']);self.assertEqual(5,out['totals']['output_tokens']);self.assertEqual(1,out['totals']['calls'])
   self.assertEqual(1,out['coverage']['missing_timestamps']);self.assertEqual('partial',out['coverage']['status'])
   self.assertNotIn('message',out)
 def test_budget_is_explicit_and_distinct_from_account_limit(self):
  m=self.mod();self.assertIsNone(m.budget_percentage(50,None));self.assertEqual(25,m.budget_percentage(50,200))
  for limit in (0,-1,True):
   with self.assertRaises(ValueError):m.budget_percentage(50,limit)
 def test_rotated_transcripts_and_cached_session_usage_do_not_duplicate_or_leak_content(self):
  m=self.mod()
  with tempfile.TemporaryDirectory() as d:
   base=Path(d);record={'sessionId':'s','message':{'role':'assistant','id':'same-call','content':'PRIVATE SYNTHETIC CONTENT','model':'observed','usage':{'input_tokens':10,'output_tokens':5}}}
   paths=[base/'part1.jsonl',base/'part2.jsonl']
   for path in paths:path.write_text(json.dumps(record)+'\n')
   report=m.aggregate_usage(paths,session_id='s');self.assertEqual(1,report['totals']['calls'])
   context={'root':str(base/'project'),'session_id':'s','cache_root':str(base/'cache')}
   m.cache_usage(context,report);self.assertEqual(15,m.read_usage(context)['session_tokens'])
   self.assertNotIn('PRIVATE SYNTHETIC', ''.join(p.read_text() for p in (base/'cache').rglob('*.json')))
if __name__=='__main__':unittest.main()
