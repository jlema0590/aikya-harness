import unittest
from aikya.core.budgets import remaining
from aikya.core.checkpoints import account,create
from pathlib import Path

class BudgetTests(unittest.TestCase):
    def setUp(self):self.ledger=create(Path.cwd(),{})
    def result(self,ident='r1',turns=3):
        return {'id':ident,'session_id':'s','cost_usd':0.01,'num_turns':turns,
                'model_usage':{'synthetic':{k:10 for k in ('inputTokens','outputTokens','cacheReadInputTokens','cacheCreationInputTokens')}}}
    def test_review_shares_total_turn_budget(self):
        account(self.ledger,self.result())
        self.assertEqual(remaining({'max_turns':5,'max_total_turns':4},self.ledger)['max_turns'],1)
    def test_duplicate_result_is_idempotent(self):
        account(self.ledger,self.result());account(self.ledger,self.result())
        self.assertEqual(remaining({'max_turns':5,'max_total_turns':4},self.ledger)['max_turns'],1)
    def test_unknown_usage_cannot_satisfy_enabled_budget(self):
        account(self.ledger,{'id':'r','session_id':'s','cost_usd':0.01})
        self.assertEqual(remaining({'max_turns':5,'max_recorded_tokens':100},self.ledger)['reason'],'token_usage_unavailable')
    def test_total_tokens_include_cache_and_limit_stops_next_query(self):
        account(self.ledger,self.result())
        self.assertEqual(remaining({'max_turns':5,'max_recorded_tokens':40},self.ledger)['reason'],'token_limit')


class DurableBudgetIntegration(unittest.TestCase):
    def test_review_is_capped_and_completed_resume_keeps_consumption(self):
        import tempfile
        from agent_loop_support import project,config,runtime
        from aikya.core.loop import run
        from aikya.core.checkpoints import load
        with tempfile.TemporaryDirectory() as folder:
            root=project(folder);delegate=runtime();requests=[]
            class CountedRuntime:
                is_sdk=False
                def available(self):return True
                def execute(self,request,on_event,cancel):
                    requests.append(request['max_turns'])
                    result=delegate.execute(request,on_event,cancel)
                    result['num_turns']=3 if request['phase']=='implement' else 1
                    return result
            raw={**config(),'max_total_turns':4}
            value=run(root,raw,CountedRuntime(),approved=True)
            self.assertEqual(value['status'],'completed',value['reason'])
            self.assertEqual(requests,[4,1])
            restored=load(root,value['run_id'])
            self.assertEqual(sum(v['num_turns'] for v in restored['results'].values()),4)
            run(root,raw,CountedRuntime(),approved=True,run_id=value['run_id'])
            self.assertEqual(requests,[4,1])
    def test_empty_usage_is_not_a_known_zero(self):
        ledger=create(Path.cwd(),{})
        account(ledger,{'id':'r','session_id':'s','cost_usd':0.01,'model_usage':{}})
        self.assertEqual(remaining({'max_turns':5,'max_recorded_tokens':100},ledger)['reason'],'token_usage_unavailable')

class BudgetBoundaryTests(unittest.TestCase):
    def test_exhausted_model_budget_still_keeps_local_validation_evidence(self):
        import tempfile
        from agent_loop_support import project,config,runtime
        from aikya.core.loop import run
        with tempfile.TemporaryDirectory() as folder:
            root=project(folder);delegate=runtime();calls=[]
            class CountedRuntime:
                is_sdk=False
                def available(self):return True
                def execute(self,request,on_event,cancel):
                    calls.append(request['phase']);value=delegate.execute(request,on_event,cancel);value['num_turns']=3;return value
            value=run(root,{**config(),'max_total_turns':3},CountedRuntime(),approved=True)
            self.assertEqual(value['reason'],'turn_limit')
            self.assertEqual(calls,['implement'])
            self.assertTrue(any(e['phase']=='Validate' and e['status']=='completed' for e in value['events']))

if __name__=='__main__':unittest.main()
